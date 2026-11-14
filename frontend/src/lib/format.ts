const mxn = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  maximumFractionDigits: 0,
  minimumFractionDigits: 0,
});

/** 12500 -> "$12,500" */
export function formatMXN(n: number): string {
  return mxn.format(n);
}
