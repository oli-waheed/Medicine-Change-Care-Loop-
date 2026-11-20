import { useEffect } from "react";
import AppShell from "./app/AppShell";
import { documentTitle, pageForPath, useCurrentPath } from "./app/navigation";
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
      {page === "not-found" && <NotFoundPage />}
    </AppShell>
  );
}

export default App;
