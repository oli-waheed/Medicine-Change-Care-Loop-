import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { CLINICAL_WORDS } from "../../test/clinicalWords";
import AboutDataPage from "./AboutDataPage";

describe("AboutDataPage", () => {
  afterEach(cleanup);

  it("states the README data-source and licence facts", () => {
    render(<AboutDataPage />);
    expect(
      screen.getByRole("heading", { level: 1, name: "About the Data" }),
    ).toBeVisible();
    for (const text of [
      /All patient and medication records in this prototype are simulated/,
      /Basic register for medicinal products \(Perusrekisteri\), Finnish Medicines Agency Fimea/,
      /Creative Commons Attribution 4\.0 \(CC BY 4\.0\)/,
      /name Fimea as the licensor/,
      /release date \(Ajopvm\) and retrieval time/,
      /The comparisons are this project’s, not Fimea’s/,
      /does not guarantee that the online data is complete or up to date/,
      /are synthetic and are not Fimea data/,
      /for pharmacist review only/,
    ]) {
      expect(screen.getByText(text)).toBeVisible();
    }
  });

  it("links to the licence and to Fimea open data", () => {
    render(<AboutDataPage />);
    expect(
      screen.getByRole("link", { name: "CC BY 4.0 licence" }),
    ).toHaveAttribute("href", "https://creativecommons.org/licenses/by/4.0/");
    expect(
      screen.getByRole("link", { name: "Fimea open data" }),
    ).toHaveAttribute("href", "https://fimea.fi/en/about_us/open-data");
  });

  it("uses no clinical wording", () => {
    render(<AboutDataPage />);
    expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);
  });
});
