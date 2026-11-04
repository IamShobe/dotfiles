/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Tailwind color names shadcn components compile to (bg-primary, text-muted-foreground, …)
      // are wired directly to theme.tsx's hex tokens — NOT the hsl(var(--x)) shadcn convention.
      // This is why: theme.tsx is the single source of truth for both light/dark (it switches
      // via prefers-color-scheme + [data-theme], never a `.dark` class), so a parallel HSL/`.dark`
      // system here would silently diverge — every shadcn component would render shadcn's stock
      // grayscale instead of the brand palette, in both themes, with no visible error. See
      // src/index.css for the (now brand-hex) light-mode fallback used only if <Theme/> isn't rendered.
      colors: {
        border: "var(--border)",
        input: "var(--border)",
        ring: "var(--brand)",
        background: "var(--bg)",
        foreground: "var(--ink)",
        primary: {
          DEFAULT: "var(--brand)",
          foreground: "#ffffff",
        },
        secondary: {
          DEFAULT: "var(--surface)",
          foreground: "var(--ink)",
        },
        destructive: {
          DEFAULT: "var(--rm)",
          foreground: "#ffffff",
        },
        muted: {
          DEFAULT: "var(--surface)",
          foreground: "var(--ink-3)",
        },
        accent: {
          DEFAULT: "var(--brand-soft)",
          foreground: "var(--brand-ink)",
        },
        popover: {
          DEFAULT: "var(--surface)",
          foreground: "var(--ink)",
        },
        card: {
          DEFAULT: "var(--surface)",
          foreground: "var(--ink)",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
