// Feature 004 T047–T052: the Medicine Catalogue page against API responses
// captured from the real backend (src/test/catalogueResponses.json).
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../../App";
import {
  catalogueFetch,
  catalogueResponse,
  unavailableFetch,
} from "../../test/catalogueFixtures";
import { CLINICAL_WORDS } from "../../test/clinicalWords";

const API = "/api/medicine-catalogue";

function renderCatalogue() {
  window.history.replaceState(null, "", "/medicine-catalogue");
  return render(<App />);
}

async function loaded() {
  await screen.findByText("Showing 1–4 of 4 packages");
}

function resultButton(pakkaustunnus: string) {
  return screen.getByRole("button", { name: new RegExp(pakkaustunnus) });
}

function cells(row: HTMLElement) {
  return Array.from((row as HTMLTableRowElement).cells).map(
    (cell) => cell.textContent,
  );
}

function detail() {
  return screen.getByRole("region", { name: "Catalogue record details" });
}

describe("Medicine Catalogue (feature 004)", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn(async (url: string) => catalogueFetch(url));
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.unstubAllGlobals();
    window.history.replaceState(null, "", "/");
  });

  function requested() {
    return fetchMock.mock.calls.map(([url]) => String(url));
  }

  describe("navigation and page load (T047)", () => {
    it("is reachable from the sidebar and shows the active release", async () => {
      window.history.replaceState(null, "", "/about-data");
      render(<App />);
      const nav = screen.getByRole("navigation", { name: "Main navigation" });
      fireEvent.click(
        within(nav).getByRole("link", { name: "Medicine Catalogue" }),
      );
      expect(
        await screen.findByRole("heading", {
          level: 1,
          name: "Medicine Catalogue",
        }),
      ).toBeVisible();
      expect(window.location.pathname).toBe("/medicine-catalogue");
      expect(document.title).toBe(
        "Medicine Catalogue | Medicine Change Care Loop",
      );
      const release = await screen.findByRole("region", {
        name: "Active catalogue release",
      });
      expect(release).toHaveTextContent("Fimea Basic Register");
      expect(release).toHaveTextContent("2099-01-02");
      expect(release).toHaveTextContent("SIM-2099-002");
      expect(release).toHaveTextContent("current-release.xml");
      expect(release).toHaveTextContent(
        "4 packages · 3 products · 3 active substances",
      );
      await loaded();
      expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);
    });

    it("lists packages in source order with their identity and VNR apart", async () => {
      renderCatalogue();
      await loaded();
      const items = within(
        screen.getByRole("list", { name: "Catalogue packages" }),
      ).getAllByRole("button");
      expect(items.map((item) => item.textContent)).toEqual([
        expect.stringContaining("SIM-PKG-100"),
        expect.stringContaining("SIM-PKG-200"),
        expect.stringContaining("SIM-PKG-400"),
        expect.stringContaining("SIM-PKG-500"),
      ]);
      expect(items[0]).toHaveAttribute("aria-pressed", "false");
      expect(requested()).toContain(`${API}/source`);
      expect(requested()).toContain(API);
    });
  });

  describe("unavailable and unreadable states (T047, FR-009)", () => {
    it("says plainly that no validated release is available", async () => {
      fetchMock.mockImplementation(async () => unavailableFetch());
      renderCatalogue();
      expect(await screen.findByText("Catalogue unavailable")).toBeVisible();
      expect(
        screen.queryByRole("list", { name: "Catalogue packages" }),
      ).toBeNull();
      expect(
        screen.queryByRole("region", { name: "Active catalogue release" }),
      ).toBeNull();
    });

    it("raises an alert when the stored release cannot be read", async () => {
      fetchMock.mockImplementation(async () => ({
        ok: false,
        status: 503,
        json: async () => ({
          detail: {
            code: "CATALOGUE_SOURCE_UNREADABLE",
            message: "Stored capture does not match its checksum.",
          },
        }),
      }));
      renderCatalogue();
      const alert = await screen.findByRole("alert");
      expect(alert).toHaveTextContent("Source release could not be read");
      expect(alert).toHaveTextContent(
        "Stored capture does not match its checksum.",
      );
    });
  });

  describe("search and filters (T048)", () => {
    it("sends the search text and every filter as query parameters", async () => {
      renderCatalogue();
      await loaded();
      fireEvent.change(
        screen.getByRole("searchbox", { name: "Search medicines" }),
        { target: { value: " amber " } },
      );
      fireEvent.click(screen.getByText("Filters"));
      const fields: [string, string][] = [
        ["Active substance", "SIM-SA01"],
        ["ATC code starts with", "SIM-A"],
        ["Pharmaceutical form", "SIM-F01"],
        ["Administration route", "SIM-R01"],
        ["VNR", "SIM-VNR-100"],
      ];
      for (const [label, value] of fields) {
        fireEvent.change(screen.getByRole("textbox", { name: label }), {
          target: { value },
        });
      }
      fireEvent.change(
        screen.getByRole("combobox", { name: "On the market (Kaupan)" }),
        { target: { value: "1" } },
      );
      fireEvent.change(
        screen.getByRole("combobox", { name: "Not present in source" }),
        { target: { value: "route" } },
      );
      await vi.waitFor(() =>
        expect(requested()).toContain(
          `${API}?q=amber&activeSubstance=SIM-SA01&atc=SIM-A&form=SIM-F01&route=SIM-R01&vnr=SIM-VNR-100&available=1&missing=route`,
        ),
      );

      fireEvent.click(
        screen.getByRole("button", { name: "Clear search and filters" }),
      );
      expect(
        screen.getByRole("searchbox", { name: "Search medicines" }),
      ).toHaveValue("");
    });

    it("shows only the matching packages, or says that none match", async () => {
      renderCatalogue();
      await loaded();
      fireEvent.click(screen.getByText("Filters"));
      fireEvent.change(
        screen.getByRole("combobox", { name: "Not present in source" }),
        { target: { value: "vnr" } },
      );
      expect(
        await screen.findByText("Showing 1–1 of 1 packages"),
      ).toBeVisible();
      expect(resultButton("SIM-PKG-400")).toHaveTextContent(
        "VNR Not present in source",
      );

      fetchMock.mockImplementation(async (url: string) =>
        url.startsWith(`${API}?`)
          ? {
              ok: true,
              status: 200,
              json: async () => ({
                ...catalogueResponse<object>(API),
                total: 0,
                page: 1,
                pageSize: 50,
                items: [],
              }),
            }
          : catalogueFetch(url),
      );
      fireEvent.change(
        screen.getByRole("searchbox", { name: "Search medicines" }),
        { target: { value: "nothing" } },
      );
      expect(
        await screen.findByText("No packages match this search."),
      ).toBeVisible();
    });
  });

  describe("product and package details (T049)", () => {
    it("opens a package with its source fields, substances and provenance", async () => {
      renderCatalogue();
      await loaded();
      fireEvent.click(resultButton("SIM-PKG-100"));
      const pkg = await within(detail()).findByRole("article", {
        name: "Package SIM-PKG-100",
      });
      expect(resultButton("SIM-PKG-100")).toHaveAttribute(
        "aria-pressed",
        "true",
      );
      const substances = within(pkg).getByRole("table", {
        name: "Active substances of package SIM-PKG-100",
      });
      const rows = within(substances).getAllByRole("row").slice(1);
      expect(rows.map((row) => cells(row)[1])).toEqual([
        "fictional substance amber (code SIM-SA01, list SIM-SUBSTANCE)",
        "fictional substance blue (code SIM-SB01, list SIM-SUBSTANCE)",
      ]);
      const provenance = within(pkg).getByRole("region", {
        name: "Source provenance",
      });
      expect(provenance).toHaveTextContent("/Perusrekisteri/Pakkaus[1]");
      expect(provenance).toHaveTextContent("current-release.xml");
      expect(provenance).toHaveTextContent("VERIFIED");
      expect(requested()).toContain(`${API}/packages/SIM-PKG-100`);
    });

    it("opens the product of a package, with an empty route kept visible", async () => {
      renderCatalogue();
      await loaded();
      fireEvent.click(resultButton("SIM-PKG-200"));
      fireEvent.click(
        await screen.findByRole("button", {
          name: "Open product SYN-PROD-200",
        }),
      );
      const product = await within(detail()).findByRole("article", {
        name: "Product SYN-PROD-200",
      });
      const info = within(product).getByRole("region", {
        name: "Product information",
      });
      expect(within(info).getByText("Present but empty")).toHaveClass(
        "source-value--empty",
      );
      const packages = within(product).getAllByRole("button", {
        name: /^SIM-PKG-/,
      });
      expect(packages.map((button) => button.textContent)).toEqual([
        expect.stringContaining("SIM-PKG-200"),
        expect.stringContaining("SIM-PKG-500"),
      ]);
      fireEvent.click(packages[1]);
      expect(
        await within(detail()).findByRole("article", {
          name: "Package SIM-PKG-500",
        }),
      ).toBeVisible();
    });

    it("explains a package that is not in the active release", async () => {
      renderCatalogue();
      await loaded();
      fetchMock.mockImplementation(async (url: string) =>
        url.startsWith(`${API}/packages/`)
          ? {
              ok: false,
              status: 404,
              json: async () => ({
                detail: { code: "PACKAGE_NOT_FOUND", releaseId: "sha256-x" },
              }),
            }
          : catalogueFetch(url),
      );
      fireEvent.click(resultButton("SIM-PKG-100"));
      expect(await within(detail()).findByRole("alert")).toHaveTextContent(
        "This package is not in the active catalogue release.",
      );
    });
  });

  describe("active-substance explorer (T050)", () => {
    it("lists every occurrence in source order, repeats kept", async () => {
      renderCatalogue();
      await loaded();
      fireEvent.click(
        screen.getByRole("button", { name: "Active substances" }),
      );
      const table = await screen.findByRole("table", {
        name: "Occurrences of Aine=SIM-SB01",
      });
      const rows = within(table).getAllByRole("row").slice(1);
      expect(rows.map((row) => [cells(row)[0], cells(row)[2]])).toEqual([
        ["SIM-PKG-100", "2"],
        ["SIM-PKG-200", "1"],
        ["SIM-PKG-500", "1"],
      ]);

      fireEvent.change(
        screen.getByRole("searchbox", { name: "Search active substances" }),
        { target: { value: "blue" } },
      );
      await vi.waitFor(() =>
        expect(requested()).toContain(`${API}/active-substances?q=blue`),
      );

      fireEvent.click(
        within(rows[1]).getByRole("button", { name: "SIM-PKG-200" }),
      );
      expect(
        await within(detail()).findByRole("article", {
          name: "Package SIM-PKG-200",
        }),
      ).toBeVisible();
    });
  });

  describe("product comparison (T051)", () => {
    it("compares two products field by field without an equivalence claim", async () => {
      renderCatalogue();
      await loaded();
      for (const [pkg, product] of [
        ["SIM-PKG-100", "SYN-PROD-100"],
        ["SIM-PKG-200", "SYN-PROD-200"],
      ]) {
        fireEvent.click(screen.getByRole("button", { name: "Packages" }));
        fireEvent.click(
          await screen.findByRole("button", { name: new RegExp(pkg) }),
        );
        fireEvent.click(
          await screen.findByRole("button", {
            name: `Open product ${product}`,
          }),
        );
        fireEvent.click(
          await screen.findByRole("button", { name: "Add to comparison" }),
        );
      }
      expect(
        screen.getByRole("button", { name: "Compare (2)" }),
      ).toHaveAttribute("aria-pressed", "true");
      expect(
        await screen.findByText(/does not indicate therapeutic equivalence/),
      ).toBeVisible();
      const table = screen.getByRole("table", {
        name: "Source fields of the two products",
      });
      const route = within(table).getByRole("row", {
        name: /Laakevalmiste\/Antoreitti/,
      });
      expect(route).toHaveTextContent("Different");
      const cas = within(table).getByRole("row", {
        name: /VaikuttavaAine\[Aine=SIM-SB01\]\/CASnumero/,
      });
      expect(cas).toHaveTextContent("Same");
      const missing = within(table).getByRole("row", {
        name: /VaikuttavaAine\[Aine=SIM-SA01\]\/Aine/,
      });
      expect(within(missing).getByText("No occurrences")).toHaveClass(
        "source-value--no-occurrences",
      );
      expect(requested()).toContain(
        `${API}/compare?productA=SYN-PROD-100&productB=SYN-PROD-200`,
      );

      fireEvent.click(screen.getByRole("button", { name: "Remove Product B" }));
      expect(
        screen.queryByRole("table", {
          name: "Source fields of the two products",
        }),
      ).toBeNull();
    });
  });

  describe("VNR and missing-value presentation (T052)", () => {
    it("shows a missing VNR as missing and never groups that package", async () => {
      renderCatalogue();
      await loaded();
      fireEvent.click(resultButton("SIM-PKG-400"));
      const pkg = await within(detail()).findByRole("article", {
        name: "Package SIM-PKG-400",
      });
      const vnr = within(pkg).getByText("VNR").closest("div")!;
      expect(within(vnr).getByText("Not present in source")).toHaveClass(
        "source-value--missing",
      );
      expect(pkg).toHaveTextContent(
        "This package has no VNR value in the source, so it is not grouped",
      );
    });

    it("links packages sharing a VNR without merging them", async () => {
      renderCatalogue();
      await loaded();
      fireEvent.click(resultButton("SIM-PKG-200"));
      const pkg = await within(detail()).findByRole("article", {
        name: "Package SIM-PKG-200",
      });
      const identity = within(pkg).getByText(
        "Package ID (Pakkaustunnus)",
      ).parentElement!;
      expect(identity).toHaveTextContent("SIM-PKG-200");
      expect(identity).not.toHaveTextContent("SIM-VNR-200");
      const shared = within(pkg).getByRole("region", {
        name: "Packages with the same VNR",
      });
      fireEvent.click(
        within(shared).getByRole("button", { name: "SIM-PKG-500" }),
      );
      expect(
        await within(detail()).findByRole("article", {
          name: "Package SIM-PKG-500",
        }),
      ).toBeVisible();
    });
  });

  it("debounces typing into one listing request", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    renderCatalogue();
    await loaded();
    const before = requested().filter((url) => url.startsWith(`${API}?`));
    const box = screen.getByRole("searchbox", { name: "Search medicines" });
    for (const value of ["a", "am", "amb"]) {
      fireEvent.change(box, { target: { value } });
    }
    await act(async () => {
      await vi.advanceTimersByTimeAsync(400);
    });
    const after = requested().filter((url) => url.startsWith(`${API}?`));
    expect(after.length - before.length).toBe(1);
    expect(after.at(-1)).toBe(`${API}?q=amb`);
  });
});
