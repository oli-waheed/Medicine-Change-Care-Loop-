// Feature 007: recording a review on a case, and shortage review cases, against
// API responses captured from the real backend (src/test/caseReviewResponses.json).
import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import responses from "../../test/caseReviewResponses.json";
import { CLINICAL_WORDS } from "../../test/clinicalWords";
import OpenReviewCasesPage from "./OpenReviewCasesPage";
import type {
  CaseStatus,
  ReviewCase,
  ReviewStep,
  StatusEvent,
} from "./openReviewCases";

const CASES = responses as unknown as ReviewCase[];
const RELEASE_100 = CASES.find(
  (item) =>
    item.caseType !== "SHORTAGE" && item.medicineIdentifier === "SIM-PKG-100",
)!;
const SHORTAGE = CASES.find((item) => item.caseType === "SHORTAGE")!;

function reply(status: number, body: unknown) {
  return { ok: status < 400, status, json: async () => body };
}

// A small fake backend: GET lists, POST applies the step like the server.
function fakeBackend() {
  let cases = structuredClone(CASES);
  const posts: { url: string; body: ReviewStep }[] = [];
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (init?.method === "POST") {
      const body = JSON.parse(String(init.body)) as ReviewStep;
      posts.push({ url, body });
      const caseId = decodeURIComponent(url.split("/")[3]);
      const current = cases.find((item) => item.caseId === caseId)!;
      if (current.status !== body.expectedStatus) {
        return reply(409, {
          detail: {
            code: "STALE_STATUS",
            message:
              "The case's status has changed since it was loaded; reload and try again.",
          },
        });
      }
      const event: StatusEvent = {
        eventId: `EVENT-${posts.length}`,
        fromStatus: body.expectedStatus,
        toStatus: body.toStatus,
        occurredAt: `2099-01-07T0${posts.length}:00:00+00:00`,
        reviewerInitials: body.reviewerInitials,
        note: body.note,
      };
      const updated = {
        ...current,
        status: body.toStatus as CaseStatus,
        statusHistory: [...(current.statusHistory ?? []), event],
      } as ReviewCase;
      cases = cases.map((item) => (item.caseId === caseId ? updated : item));
      return reply(201, updated);
    }
    const reviewed = url.includes("includeReviewed=true");
    return reply(
      200,
      cases.filter(
        (item) => reviewed || ["NEW", "IN_PROGRESS"].includes(item.status),
      ),
    );
  });
  return { fetchMock, posts };
}

async function openCase(name: RegExp) {
  render(<OpenReviewCasesPage />);
  await screen.findByText("Cases (3)");
  const list = screen.getByRole("navigation", { name: "Open review cases" });
  const button = within(list)
    .getAllByRole("button")
    .find((item) => name.test(item.textContent ?? ""))!;
  fireEvent.click(button);
}

function review() {
  return screen.getByRole("region", { name: "Review" });
}

describe("Recording a review (feature 007)", () => {
  let backend: ReturnType<typeof fakeBackend>;

  beforeEach(() => {
    backend = fakeBackend();
    vi.stubGlobal("fetch", backend.fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("shows the status, the allowed steps and the history of a new case", async () => {
    await openCase(/SIM-PKG-100/);
    const panel = review();
    expect(
      within(panel).getByText("New", { selector: ".status-badge" }),
    ).toBeVisible();
    expect(
      within(panel)
        .getAllByRole("button")
        .map((button) => button.textContent),
    ).toEqual([
      "Mark in progress",
      "Reviewed – no action needed",
      "Reviewed – follow-up needed",
    ]);
    const history = within(panel).getByRole("list", { name: "Review history" });
    expect(within(history).getAllByRole("listitem")).toHaveLength(1);
    expect(history).toHaveTextContent("Case created: New");
  });

  it("records in progress, then a reviewed outcome that leaves the open list", async () => {
    await openCase(/SIM-PKG-100/);
    fireEvent.change(screen.getByRole("textbox", { name: "Your initials" }), {
      target: { value: "AB" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Mark in progress" }));
    expect(
      await screen.findByText(
        "Recorded for Fictional Product Amber: Mark in progress. Status: In progress.",
      ),
    ).toBeVisible();
    expect(backend.posts[0]).toEqual({
      url: `/api/review-cases/${encodeURIComponent(RELEASE_100.caseId)}/status-events`,
      body: {
        expectedStatus: "NEW",
        toStatus: "IN_PROGRESS",
        reviewerInitials: "AB",
        note: null,
      },
    });
    const list = screen.getByRole("navigation", { name: "Open review cases" });
    expect(within(list).getByText("In progress")).toBeVisible();

    // The initials stay filled in; the note is required for an outcome.
    fireEvent.change(screen.getByRole("textbox", { name: "Note" }), {
      target: { value: "Label text checked." },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Reviewed – no action needed" }),
    );
    expect(
      await screen.findByText(/Status: Reviewed – no action needed\./),
    ).toBeVisible();
    expect(backend.posts[1].body).toEqual({
      expectedStatus: "IN_PROGRESS",
      toStatus: "REVIEWED_NO_ACTION",
      reviewerInitials: "AB",
      note: "Label text checked.",
    });
    expect(screen.getByText("Cases (2)")).toBeVisible();
    expect(
      within(screen.getByRole("navigation", { name: "Open review cases" }))
        .queryAllByRole("button")
        .some((button) => /SIM-PKG-100/.test(button.textContent ?? "")),
    ).toBe(false);
  });

  it("shows reviewed cases on request, with their history, and can reopen them", async () => {
    await openCase(/SIM-PKG-100/);
    fireEvent.change(screen.getByRole("textbox", { name: "Your initials" }), {
      target: { value: "CD" },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "Note" }), {
      target: { value: "Ask the team." },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Reviewed – follow-up needed" }),
    );
    await screen.findByText("Cases (2)");

    fireEvent.click(
      screen.getByRole("checkbox", { name: "Show reviewed cases" }),
    );
    await screen.findByText("Cases (3)");
    expect(backend.fetchMock).toHaveBeenCalledWith(
      "/api/open-review-cases?includeReviewed=true",
      expect.anything(),
    );
    const list = screen.getByRole("navigation", { name: "Open review cases" });
    fireEvent.click(
      within(list)
        .getAllByRole("button")
        .find((button) => /SIM-PKG-100/.test(button.textContent ?? ""))!,
    );
    const panel = review();
    const history = within(panel).getByRole("list", { name: "Review history" });
    expect(history).toHaveTextContent("New → Reviewed – follow-up needed");
    expect(history).toHaveTextContent("by CD");
    expect(history).toHaveTextContent("Ask the team.");
    expect(
      within(panel)
        .getAllByRole("button")
        .map((button) => button.textContent),
    ).toEqual(["Reopen"]);
    expect(
      within(panel).getByText("Required to reopen a reviewed case."),
    ).toBeVisible();
  });

  it("shows the server's reason when a step is refused", async () => {
    await openCase(/SIM-PKG-100/);
    backend.fetchMock.mockImplementationOnce(async () =>
      reply(422, {
        detail: {
          code: "INVALID_REVIEW_STEP",
          message: "A note is required for this review step.",
        },
      }),
    );
    fireEvent.change(screen.getByRole("textbox", { name: "Your initials" }), {
      target: { value: "AB" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Reviewed – no action needed" }),
    );
    expect(await within(review()).findByRole("alert")).toHaveTextContent(
      "A note is required for this review step.",
    );
    expect(
      within(review()).getByText("New", { selector: ".status-badge" }),
    ).toBeVisible();
  });
});

describe("Shortage review cases (feature 007)", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", fakeBackend().fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("lists the shortage case with its kind and changed column", async () => {
    render(<OpenReviewCasesPage />);
    await screen.findByText("Cases (3)");
    const list = screen.getByRole("navigation", { name: "Open review cases" });
    const item = within(list)
      .getAllByRole("button")
      .find((button) => button.textContent?.includes("Shortage changed"))!;
    expect(item).toHaveClass("case-list-item--shortage");
    expect(item).toHaveTextContent("Shortage changed: Valid");
    expect(item).toHaveTextContent(SHORTAGE.medicineIdentifier);
  });

  it("shows the shortage row as published, its source files and the notice", async () => {
    await openCase(/Shortage changed/);
    const article = screen.getByRole("article", {
      name: `Evidence for ${SHORTAGE.caseId}`,
    });
    expect(
      within(article).getByText("Shortage", { selector: ".change-kind-badge" }),
    ).toBeVisible();
    const change = within(article).getByRole("region", {
      name: "Shortage change",
    });
    expect(change).toHaveTextContent("VNR SIM-VNR-500");
    expect(change).toHaveTextContent("Fictional Product Blue");
    expect(change).toHaveTextContent("Package ID SIM-PKG-500");
    expect(change).toHaveTextContent("catalogue release 2099-01-02");

    const table = within(change).getByRole("table", {
      name: "Shortage row before and after, as published",
    });
    const valid = within(table).getByRole("row", { name: /Valid/ });
    expect(valid).toHaveClass("shortage-change-row--changed");
    expect(
      Array.from((valid as HTMLTableRowElement).cells).map(
        (cell) => cell.textContent,
      ),
    ).toEqual(["ValidChanged", "E", "K"]);
    expect(change).toHaveTextContent(
      "Dates and status are the company's report to Fimea, shown as published; the end date is an estimate.",
    );

    const sources = within(article).getByRole("region", {
      name: "Source evidence",
    });
    const prior = within(sources).getByRole("region", {
      name: "Previous file source evidence",
    });
    expect(prior).toHaveTextContent("Shortages.txt");
    expect(prior).toHaveTextContent(SHORTAGE.sources.prior.checksum);
    expect(prior).toHaveTextContent("Line4");
    expect(prior).toHaveTextContent("2099-01-05 04:00 UTC");
    expect(prior).toHaveTextContent("CC BY 4.0");

    expect(
      within(article).getByRole("region", { name: "Review" }),
    ).toBeVisible();
    expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);
  });

  it("shows a shortage that ended as not in the current file", async () => {
    const ended = structuredClone(SHORTAGE) as Extract<
      ReviewCase,
      { caseType: "SHORTAGE" }
    >;
    ended.shortageChange.kind = "SHORTAGE_ENDED";
    ended.shortageChange.changedColumns = [];
    ended.shortageChange.after = null;
    ended.sources.current.lineNumber = null;
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => reply(200, [ended])),
    );
    render(<OpenReviewCasesPage />);
    await screen.findByText("Cases (1)");
    const table = screen.getByRole("table", {
      name: "Shortage row before and after, as published",
    });
    expect(within(table).getAllByText("Not in file")).toHaveLength(6);
    expect(
      screen.getByRole("heading", { name: "Shortage ended" }),
    ).toBeVisible();
    expect(
      screen.getByRole("region", { name: "Current file source evidence" }),
    ).toHaveTextContent("Not in this file");
  });
});
