// Feature 015: linked records of a package or product, against responses
// captured from the real backend over the synthetic links release.
import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { catalogueFetch } from "../../test/catalogueFixtures";
import { CLINICAL_WORDS } from "../../test/clinicalWords";
import LinkedRecordsCard from "./LinkedRecordsCard";

function group(name: string) {
  return screen.getByRole("listitem", { name });
}

describe("Linked records (feature 015)", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn(async (url: string) => catalogueFetch(url));
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("groups links by how certain they are and opens linked records", async () => {
    const openPackage = vi.fn();
    const openProduct = vi.fn();
    render(
      <LinkedRecordsCard
        kind="package"
        id="SIM-PKG-L11"
        onOpenPackage={openPackage}
        onOpenProduct={openProduct}
      />,
    );
    const vnr = await screen.findByRole("listitem", {
      name: "Other packages with the same VNR",
    });
    expect(within(vnr).getByText("Verified link")).toBeVisible();
    fireEvent.click(within(vnr).getByRole("button", { name: "SIM-PKG-L21" }));
    expect(openPackage).toHaveBeenCalledWith("SIM-PKG-L21");

    const strengths = group(
      "Products with the same active substances (other strengths and forms)",
    );
    expect(strengths).toHaveTextContent("synthetic strength 20");
    fireEvent.click(
      within(strengths).getByRole("button", { name: "SYN-PROD-L2" }),
    );
    expect(openProduct).toHaveBeenCalledWith("SYN-PROD-L2");

    const similar = group("Holder written differently");
    expect(within(similar).getByText("Possible link")).toBeVisible();
    expect(similar).toHaveTextContent("fictional pharma OY");

    const shortages = group("Shortages reported to Fimea");
    expect(shortages).toHaveTextContent("VNR SIM-VNR-200 · Valid K");
    expect(
      screen.getByText(
        /say nothing about whether one product can be used in place/,
      ),
    ).toBeVisible();
    expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);
    for (const [url, options] of fetchMock.mock.calls) {
      expect(String(url)).toBe(
        "/api/medicine-catalogue/packages/SIM-PKG-L11/links",
      );
      expect(options?.method ?? "GET").toBe("GET");
    }
  });

  it("names identifiers that are missing in the source", async () => {
    render(
      <LinkedRecordsCard
        kind="package"
        id="SIM-PKG-L41"
        onOpenPackage={vi.fn()}
      />,
    );
    const vnr = await screen.findByRole("listitem", {
      name: "Other packages with the same VNR",
    });
    expect(within(vnr).getByText("Missing: cannot be linked")).toBeVisible();
    expect(vnr).toHaveTextContent("No VNR in the source");
    expect(
      within(group("Shortages reported to Fimea")).getByText(
        "Missing: cannot be linked",
      ),
    ).toBeVisible();
    const byName = group("Products with an active substance of the same name");
    expect(within(byName).getByText("Possible link")).toBeVisible();
    // Without an open-product action, product references are shown as text.
    expect(within(byName).queryByRole("button")).toBeNull();
    expect(byName).toHaveTextContent("SYN-PROD-L5");
  });

  it("covers every package of a product", async () => {
    render(
      <LinkedRecordsCard
        kind="product"
        id="SYN-PROD-L1"
        onOpenPackage={vi.fn()}
      />,
    );
    const vnr = await screen.findByRole("listitem", {
      name: "Other packages with the same VNR",
    });
    expect(
      within(vnr).getByRole("button", { name: "SIM-PKG-L21" }),
    ).toBeVisible();
    expect(fetchMock.mock.calls[0][0]).toBe(
      "/api/medicine-catalogue/products/SYN-PROD-L1/links",
    );
  });

  it("folds long groups to five records", async () => {
    const item = (n: number) => ({
      productReference: `SYN-PROD-F${n}`,
      name: { state: "value", value: `Fictional Fold ${n}`, attributes: {} },
      strength: { state: "value", value: "synthetic strength", attributes: {} },
      form: { state: "value", value: "fictional form", attributes: {} },
      holders: [],
      packageCount: 1,
    });
    fetchMock.mockImplementation(async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        releaseId: "synthetic",
        anchorPackages: ["SIM-PKG-F0"],
        shortageSource: null,
        notice:
          "Links show shared identifiers and values in Fimea's source only.",
        groups: [
          {
            id: "SAME_HOLDER",
            label: "Other products of the same holder",
            certainty: "VERIFIED",
            basis: "Exactly the same holder text.",
            itemKind: "product",
            total: 60,
            items: Array.from({ length: 7 }, (_, n) => item(n)),
            note: null,
          },
        ],
      }),
    }));
    render(
      <LinkedRecordsCard
        kind="package"
        id="SIM-PKG-F0"
        onOpenPackage={vi.fn()}
      />,
    );
    const holder = await screen.findByRole("listitem", {
      name: "Other products of the same holder",
    });
    expect(within(holder).getAllByRole("listitem")).toHaveLength(5);
    expect(holder).toHaveTextContent("Showing 5 of 60.");
    const toggle = within(holder).getByRole("button", {
      name: "Show more (2)",
    });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(toggle);
    expect(within(holder).getAllByRole("listitem")).toHaveLength(7);
    expect(holder).toHaveTextContent("Showing 7 of 60.");
    fireEvent.click(within(holder).getByRole("button", { name: "Show fewer" }));
    expect(within(holder).getAllByRole("listitem")).toHaveLength(5);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("says when nothing is linked and when loading fails", async () => {
    render(
      <LinkedRecordsCard
        kind="package"
        id="SIM-PKG-100"
        onOpenPackage={vi.fn()}
      />,
    );
    expect(await screen.findByText("No linked records.")).toBeVisible();
    cleanup();
    fetchMock.mockImplementation(async () => ({
      ok: false,
      status: 503,
      json: async () => ({ detail: { code: "CATALOGUE_UNAVAILABLE" } }),
    }));
    render(
      <LinkedRecordsCard
        kind="package"
        id="SIM-PKG-L11"
        onOpenPackage={vi.fn()}
      />,
    );
    expect(
      await screen.findByText("Linked records could not be loaded."),
    ).toBeVisible();
  });
});
