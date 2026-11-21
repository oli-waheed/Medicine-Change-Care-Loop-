import { useEffect } from "react";
import AppShell from "./app/AppShell";
import { documentTitle, pageForPath, useCurrentPath } from "./app/navigation";
import AboutDataPage from "./pages/about-data/AboutDataPage";
import MedicineCataloguePage from "./pages/medicine-catalogue/MedicineCataloguePage";
import MedicineShortagesPage from "./pages/medicine-shortages/MedicineShortagesPage";
import NotFoundPage from "./pages/not-found/NotFoundPage";
import OpenReviewCasesPage from "./pages/open-review-cases/OpenReviewCasesPage";

function App() {
  const page = pageForPath(useCurrentPath());

  useEffect(() => {
    document.title = documentTitle(page);
  }, [page]);

  return (
    <AppShell currentPage={page}>
      {page === "open-review-cases" && <OpenReviewCasesPage />}
      {page === "medicine-catalogue" && <MedicineCataloguePage />}
      {page === "medicine-shortages" && <MedicineShortagesPage />}
      {page === "about-data" && <AboutDataPage />}
      {page === "not-found" && <NotFoundPage />}
    </AppShell>
  );
}

export default App;
