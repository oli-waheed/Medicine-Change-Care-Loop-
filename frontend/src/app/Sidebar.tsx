import { appVersion } from "./appVersion";
import {
  BrandMark,
  CasesIcon,
  CatalogueIcon,
  ChevronIcon,
  DataIcon,
  ShortageIcon,
} from "./icons";
import {
  NAVIGATION_ITEMS,
  PRODUCT_NAME,
  handleLinkClick,
  type PageId,
} from "./navigation";

const ICONS = {
  "open-review-cases": CasesIcon,
  "medicine-catalogue": CatalogueIcon,
  "medicine-shortages": ShortageIcon,
  "about-data": DataIcon,
} as const;

export const LICENCE_URL = "https://creativecommons.org/licenses/by/4.0/";
export const FIMEA_OPEN_DATA_URL = "https://fimea.fi/en/about_us/open-data";

export default function Sidebar({
  currentPage,
  expanded,
  onToggle,
  onNavigate,
}: {
  currentPage: PageId;
  expanded: boolean;
  onToggle: (opener: HTMLElement) => void;
  onNavigate: () => void;
}) {
  return (
    <div className="sidebar">
      <div className="sidebar-brand">
        <BrandMark className="sidebar-brand-mark" />
        <span className="sidebar-brand-name">{PRODUCT_NAME}</span>
        {/* Shown only on tablet widths, where the sidebar collapses to icons. */}
        <button
          type="button"
          className="sidebar-rail-toggle"
          aria-expanded={expanded}
          aria-controls="app-sidebar"
          title={expanded ? "Collapse sidebar" : "Expand sidebar"}
          onClick={(event) => onToggle(event.currentTarget)}
        >
          <ChevronIcon />
          <span className="visually-hidden">Sidebar</span>
        </button>
      </div>

      <nav className="sidebar-nav" aria-label="Main navigation">
        <ul>
          {NAVIGATION_ITEMS.map((item) => {
            const Icon = ICONS[item.page];
            const current = item.page === currentPage;
            return (
              <li key={item.page}>
                <a
                  href={item.path}
                  className={`sidebar-link${current ? " sidebar-link--current" : ""}`}
                  aria-current={current ? "page" : undefined}
                  title={item.label}
                  onClick={(event) =>
                    handleLinkClick(event, item.path, onNavigate)
                  }
                >
                  <Icon className="sidebar-link-icon" />
                  <span className="sidebar-link-label">{item.label}</span>
                </a>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="sidebar-footer">
        <p className="sidebar-attribution">
          Source data: Basic register for medicinal products, Finnish Medicines
          Agency Fimea.{" "}
          <a href={LICENCE_URL} rel="noreferrer">
            CC BY 4.0
          </a>
        </p>
        {appVersion && <p className="sidebar-version">Version {appVersion}</p>}
      </div>
    </div>
  );
}
