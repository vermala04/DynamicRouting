// CEVA brand tokens — used by Recharts/Leaflet where Tailwind classes can't reach.
export const CEVA = {
  red: "#98012E",
  redDark: "#7A0124",
  black: "#231F20",
  navy: "#0B2C5C",
  navyDark: "#081F40",
  gray: "#F5F5F7",
  grayMid: "#E5E5EA",
  grayText: "#6B6B72",
  green: "#1B7F3A",
  amber: "#E5A100",
};

// 8 distinct route colors (one per vehicle).
export const ROUTE_COLORS = [
  "#98012E", // CEVA red
  "#0B2C5C", // navy
  "#1B7F3A", // green
  "#E5A100", // amber
  "#7C3AED", // violet
  "#0EA5E9", // sky
  "#DB2777", // pink
  "#475569", // slate
];

export const fmtINR = (n: number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n || 0);

export const fmtNum = (n: number, d = 1) =>
  new Intl.NumberFormat("en-IN", { maximumFractionDigits: d }).format(n || 0);

export const minutesToHHMM = (mins: number) => {
  const h = Math.floor(mins / 60);
  const m = Math.floor(mins % 60);
  return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}`;
};
