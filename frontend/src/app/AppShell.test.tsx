import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";

function renderAt(path: string) {
  window.history.replaceState(null, "", path);
  return render(<App />);
}

function sidebarLinks() {
  return within(
    screen.getByRole("navigation", { name: "Main navigation" }),
  ).getAllByRole("link");
}

function navigateByHistory(path: string) {
  act(() => {
    window.history.pushState(null, "", path);
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
}

describe("Application shell (feature 003)", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => [] });
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    window.history.replaceState(null, "", "/");
  });

  describe("sidebar and navigation", () => {
    it("shows the product name, one working link and attribution, with no theme switch", async () => {
      renderAt("/");
      await screen.findByText("There are no NEW review cases.");

      const sidebar = screen.getByRole("complementary", { name: "Sidebar" });

      expect(
        within(sidebar).getByText("Medicine Change Care Loop"),
      ).toBeInTheDocument();

      expect(sidebarLinks().map((link) => link.textContent)).toEqual([
        "Open Review Cases",
      ]);

      expect(screen.queryByRole("switch")).toBeNull();
      expect(document.documentElement).not.toHaveAttribute("data-theme");

      expect(
        within(sidebar).getByText(/Basic register for medicinal products/),
      ).toBeInTheDocument();

      expect(
        within(sidebar).getByRole("link", { name: "CC BY 4.0" }),
      ).toHaveAttribute("href", "https://creativecommons.org/licenses/by/4.0/");
    });

    it("hides the placeholder version 0.0.0", async () => {
      renderAt("/");
      await screen.findByText("There are no NEW review cases.");
      expect(screen.queryByText(/^Version /)).toBeNull();
    });

    it("marks Open Review Cases as the current page", async () => {
      renderAt("/");
      await screen.findByText("There are no NEW review cases.");

      expect(document.title).toBe(
        "Open Review Cases | Medicine Change Care Loop",
      );

      expect(sidebarLinks()).toHaveLength(1);
      expect(sidebarLinks()[0]).toHaveAttribute("aria-current", "page");
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("shows Page not found for the unimplemented About the Data route", () => {
      renderAt("/about-data");

      expect(
        screen.getByRole("heading", { level: 1, name: "Page not found" }),
      ).toBeVisible();

      expect(document.title).toBe("Page not found | Medicine Change Care Loop");
      expect(sidebarLinks()).toHaveLength(1);
      expect(sidebarLinks()[0]).not.toHaveAttribute("aria-current");
      expect(fetchMock).not.toHaveBeenCalled();
    });

    it("shows Page not found for an unknown address, with a way back", async () => {
      renderAt("/dashboard");

      expect(
        screen.getByRole("heading", { level: 1, name: "Page not found" }),
      ).toBeVisible();

      expect(document.title).toBe("Page not found | Medicine Change Care Loop");

      for (const link of sidebarLinks()) {
        expect(link).not.toHaveAttribute("aria-current");
      }

      const main = screen.getByRole("main");

      fireEvent.click(
        within(main).getByRole("link", { name: "Open Review Cases" }),
      );

      expect(
        await screen.findByRole("heading", {
          level: 1,
          name: "Open review cases",
        }),
      ).toBeVisible();

      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("leaves modified clicks to the browser", async () => {
      renderAt("/");
      await screen.findByText("There are no NEW review cases.");

      fireEvent.click(sidebarLinks()[0], { ctrlKey: true });

      expect(window.location.pathname).toBe("/");
    });
  });

  describe("navigation toggle and keyboard access", () => {
    it("does not move focus on first load, but does after a route change", async () => {
      renderAt("/");
      await screen.findByText("There are no NEW review cases.");

      expect(document.body).toHaveFocus();

      navigateByHistory("/unknown");

      expect(
        await screen.findByRole("heading", {
          level: 1,
          name: "Page not found",
        }),
      ).toBeVisible();

      expect(screen.getByRole("main")).toHaveFocus();
    });

    it("starts with a skip link that moves focus to the main content", () => {
      renderAt("/about-data");

      const skip = screen.getByRole("link", {
        name: "Skip to main content",
      });

      const focusable = document.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
      );

      expect(focusable[0]).toBe(skip);

      fireEvent.click(skip);

      expect(screen.getByRole("main")).toHaveFocus();
    });

    it("opens and closes the navigation with focus management", () => {
      renderAt("/");

      const menu = screen.getByRole("button", { name: "Menu" });

      expect(menu).toHaveAttribute("aria-expanded", "false");
      expect(menu).toHaveAttribute("aria-controls", "app-sidebar");

      fireEvent.click(menu);

      expect(menu).toHaveAttribute("aria-expanded", "true");
      expect(sidebarLinks()[0]).toHaveFocus();

      expect(screen.getByRole("main", { hidden: true })).toHaveAttribute(
        "inert",
      );

      fireEvent.keyDown(document, { key: "Escape" });

      expect(menu).toHaveAttribute("aria-expanded", "false");
      expect(menu).toHaveFocus();
      expect(screen.getByRole("main")).not.toHaveAttribute("inert");

      fireEvent.click(menu);
      fireEvent.click(menu);

      expect(menu).toHaveAttribute("aria-expanded", "false");
      expect(menu).toHaveFocus();
    });

    it("keeps Tab inside the open navigation", () => {
      renderAt("/");

      fireEvent.click(screen.getByRole("button", { name: "Menu" }));

      const sidebar = document.getElementById("app-sidebar")!;
      const items = Array.from(
        sidebar.querySelectorAll<HTMLElement>("a[href], button"),
      );

      const first = items[0];
      const last = items[items.length - 1];

      last.focus();
      fireEvent.keyDown(last, { key: "Tab" });
      expect(first).toHaveFocus();

      fireEvent.keyDown(first, { key: "Tab", shiftKey: true });
      expect(last).toHaveFocus();
    });

    it("closes the navigation after following the Open Review Cases link", async () => {
      renderAt("/unknown");

      const menu = screen.getByRole("button", { name: "Menu" });

      fireEvent.click(menu);
      fireEvent.click(sidebarLinks()[0]);

      expect(menu).toHaveAttribute("aria-expanded", "false");

      expect(
        await screen.findByText("There are no NEW review cases."),
      ).toBeVisible();
    });

    it("expands and collapses the tablet sidebar with its own toggle", () => {
      renderAt("/");

      const sidebar = screen.getByRole("complementary", { name: "Sidebar" });
      const rail = within(sidebar).getByRole("button", { name: "Sidebar" });

      expect(rail).toHaveAttribute("aria-expanded", "false");
      expect(rail).toHaveAttribute("aria-controls", "app-sidebar");

      fireEvent.click(rail);

      expect(rail).toHaveAttribute("aria-expanded", "true");
      expect(sidebarLinks()[0]).toHaveFocus();

      expect(screen.getByRole("main", { hidden: true })).toHaveAttribute(
        "inert",
      );

      fireEvent.keyDown(document, { key: "Escape" });

      expect(rail).toHaveAttribute("aria-expanded", "false");
      expect(rail).toHaveFocus();

      fireEvent.click(rail);
      fireEvent.click(rail);

      expect(rail).toHaveAttribute("aria-expanded", "false");
      expect(rail).toHaveFocus();
    });

    it("closes the navigation when the scrim is clicked", () => {
      renderAt("/");

      const menu = screen.getByRole("button", { name: "Menu" });

      fireEvent.click(menu);
      fireEvent.click(screen.getByTestId("navigation-scrim"));

      expect(menu).toHaveAttribute("aria-expanded", "false");
    });
  });
});
