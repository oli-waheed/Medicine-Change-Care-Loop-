import { useEffect, useRef, type ReactNode } from "react";
import { MenuIcon } from "./icons";
import { PRODUCT_NAME, type PageId } from "./navigation";
import Sidebar from "./Sidebar";
import { useNavigationDrawer } from "./useNavigationDrawer";
import "./AppShell.css";

export default function AppShell({
  currentPage,
  children,
}: {
  currentPage: PageId;
  children: ReactNode;
}) {
  const { open, toggle, close, drawerRef, onDrawerKeyDown } =
    useNavigationDrawer();
  const mainRef = useRef<HTMLElement>(null);
  const shownPage = useRef(currentPage);

  // After moving to another page, start reading at the new page's content.
  // Comparing with the previously shown page keeps the initial load (and
  // React StrictMode's repeated effects) from moving focus.
  useEffect(() => {
    if (shownPage.current === currentPage) return;
    shownPage.current = currentPage;
    mainRef.current?.focus();
  }, [currentPage]);

  return (
    <div className={`app-shell${open ? " app-shell--drawer-open" : ""}`}>
      <a
        className="skip-link"
        href="#main-content"
        onClick={(event) => {
          event.preventDefault();
          mainRef.current?.focus();
        }}
      >
        Skip to main content
      </a>

      <header className="app-topbar">
        <button
          type="button"
          className="app-menu-toggle"
          aria-expanded={open}
          aria-controls="app-sidebar"
          onClick={(event) => toggle(event.currentTarget)}
        >
          <MenuIcon />
          <span>Menu</span>
        </button>
        <span className="app-topbar-brand">{PRODUCT_NAME}</span>
      </header>

      <aside
        id="app-sidebar"
        ref={drawerRef}
        className={`app-sidebar${open ? " app-sidebar--open" : ""}`}
        aria-label="Sidebar"
        onKeyDown={onDrawerKeyDown}
      >
        <Sidebar
          currentPage={currentPage}
          expanded={open}
          onToggle={toggle}
          onNavigate={() => close(false)}
        />
      </aside>

      {open && (
        <div
          className="app-scrim"
          data-testid="navigation-scrim"
          aria-hidden="true"
          onClick={() => close(true)}
        />
      )}

      <main
        id="main-content"
        ref={mainRef}
        tabIndex={-1}
        className="app-main"
        inert={open}
      >
        {children}
      </main>
    </div>
  );
}
