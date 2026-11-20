import { handleLinkClick } from "../../app/navigation";

export default function NotFoundPage() {
  return (
    <div className="not-found-page">
      <header className="page-header">
        <h1>Page not found</h1>
        <p className="page-description">There is no page at this address.</p>
      </header>
      <p>
        <a href="/" onClick={(event) => handleLinkClick(event, "/")}>
          Open Review Cases
        </a>
      </p>
    </div>
  );
}
