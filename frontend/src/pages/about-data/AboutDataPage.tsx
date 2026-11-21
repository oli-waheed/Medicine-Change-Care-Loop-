import { FIMEA_OPEN_DATA_URL, LICENCE_URL } from "../../app/Sidebar";
import "./AboutDataPage.css";
import LatestReleaseCheck from "./LatestReleaseCheck";

// Restates the README "Data Source and Licence" section; adds no new claims.
export default function AboutDataPage() {
  return (
    <div className="about-page">
      <header className="page-header">
        <p className="eyebrow">Medicine Change Care Loop</p>
        <h1>About the Data</h1>
        <p className="page-description">
          Where the information in this prototype comes from, how it may be
          shared, and its limits.
        </p>
      </header>

      <div className="about-grid">
        <section className="about-card" aria-labelledby="about-simulated">
          <h2 id="about-simulated">Simulated records</h2>
          <p>
            All patient and medication records in this prototype are simulated.
            No real patient information is used.
          </p>
          <p>
            The test fixtures in <code>tests/fixtures/</code> are synthetic and
            are not Fimea data.
          </p>
        </section>

        <section className="about-card" aria-labelledby="about-source">
          <h2 id="about-source">Source data</h2>
          <p>
            Basic register for medicinal products (Perusrekisteri), Finnish
            Medicines Agency Fimea, published as open data under the Creative
            Commons Attribution 4.0 (CC BY 4.0) licence.
          </p>
          <p>
            Medicine Shortages shows Fimea’s open-data shortage file
            (Shortages.txt), published under the same licence.
          </p>
          <ul className="about-links">
            <li>
              <a href={LICENCE_URL} rel="noreferrer">
                CC BY 4.0 licence
              </a>
            </li>
            <li>
              <a href={FIMEA_OPEN_DATA_URL} rel="noreferrer">
                Fimea open data
              </a>
            </li>
          </ul>
        </section>

        <LatestReleaseCheck />

        <section className="about-card" aria-labelledby="about-attribution">
          <h2 id="about-attribution">Attribution</h2>
          <p>
            When presenting or sharing results, name Fimea as the licensor, the
            material (“Basic register for medicinal products”) and the release
            date of the data used.
          </p>
          <p>
            Each review case shows the release date (Ajopvm) and retrieval time
            of its source files.
          </p>
        </section>

        <section className="about-card" aria-labelledby="about-changes">
          <h2 id="about-changes">What this project changes</h2>
          <p>
            This project normalises selected fields and compares successive
            releases. The comparisons are this project’s, not Fimea’s.
          </p>
        </section>

        <section className="about-card" aria-labelledby="about-limits">
          <h2 id="about-limits">Limitations</h2>
          <p>
            Fimea notes that individual errors may occur in the register and
            does not guarantee that the online data is complete or up to date.
          </p>
        </section>

        <section className="about-card" aria-labelledby="about-review">
          <h2 id="about-review">Review only</h2>
          <p>
            This application presents source information for pharmacist review
            only. It does not make clinical decisions.
          </p>
        </section>
      </div>
    </div>
  );
}
