// Feature 016: supply signals, against responses captured from the real
// backend (src/test/supplySignalsResponses.json; asOf fixed to 2099-01-21).
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
import SupplySignalsCard from "./SupplySignalsCard";

function card() {
  return screen.getByRole("region", { name: "Supply signals" });
}

describe("Supply signals (feature 016)", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn(async (url: string) => catalogueFetch(url));
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("shows the listed row with day counts, listings and related products", async () => {
    const openProduct = vi.fn();
    render(
      <SupplySignalsCard
        kind="package"
        id="SIM-PKG-L11"
        onOpenProduct={openProduct}
      />,
    );
    expect(
      await within(card()).findByText(/^Listed in Fimea's shortage file/),
    ).toBeVisible();
    const rows = within(card()).getByRole("list", {
      name: "Rows in the shortage file now",
    });
    expect(rows).toHaveTextContent(
      "Unavailable from 2099-01-01 (20 days ago) · Estimated end 2099-03-31 (in 69 days)",
    );
    expect(card()).toHaveTextContent("Days are counted to 2099-01-21.");
    const listings = within(card()).getByRole("table", {
      name: "Listings in downloaded shortage files",
    });
    expect(within(listings).getAllByRole("row")[1]).toHaveTextContent(
      "SIM-VNR-2002099-01-01 05:00 UTC2099-01-02 05:00 UTC2Yes",
    );
    expect(card()).toHaveTextContent(
      "1 of 1 have a VNR listed in the shortage file now.",
    );
    fireEvent.click(
      within(card()).getByRole("button", { name: "SYN-PROD-L2" }),
    );
    expect(openProduct).toHaveBeenCalledWith("SYN-PROD-L2");
    expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      "/api/medicine-catalogue/packages/SIM-PKG-L11/supply-signals",
    ]);
  });

  it("never turns not listed into available", async () => {
    render(
      <SupplySignalsCard
        kind="package"
        id="SIM-PKG-L12"
        onOpenProduct={vi.fn()}
      />,
    );
    expect(
      await within(card()).findByText(
        /This does not show that it is available\.$/,
      ),
    ).toBeVisible();
    expect(card()).toHaveTextContent("Never listed in a downloaded file.");
  });

  it("explains a missing VNR", async () => {
    render(<SupplySignalsCard kind="package" id="SIM-PKG-L41" />);
    expect(
      await within(card()).findByText(
        "No VNR in the source, so Fimea's shortage file cannot be linked.",
      ),
    ).toBeVisible();
    expect(within(card()).queryByRole("table")).toBeNull();
  });

  it("shows an ended listing and recorded register changes", async () => {
    render(<SupplySignalsCard kind="package" id="SIM-PKG-100" />);
    await within(card()).findByText(/^Not listed/);
    const listings = within(card()).getByRole("table", {
      name: "Listings in downloaded shortage files",
    });
    expect(within(listings).getAllByRole("row")[1]).toHaveTextContent("1No");
    expect(card()).toHaveTextContent(
      "2099-01-02 → 2099-01-09 · SIM-PKG-100 · Pakkaus/Kaupanolo/Kaupan: 1 → 0",
    );
  });

  it("covers a product's packages and reports load errors", async () => {
    render(<SupplySignalsCard kind="product" id="SYN-PROD-L1" />);
    await within(card()).findByText(/^Listed in Fimea/);
    expect(card()).toHaveTextContent("SIM-PKG-L11");
    expect(card()).toHaveTextContent("SIM-PKG-L12");
    // Without an open-product action, related products are text.
    expect(within(card()).queryByRole("button")).toBeNull();
    cleanup();
    render(<SupplySignalsCard kind="package" id="SIM-PKG-NONE" />);
    expect(
      await screen.findByText("Supply signals could not be loaded."),
    ).toBeVisible();
  });
});
