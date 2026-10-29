import { COMPANY_TZ, formatDate, parseDate, todayIso } from "./dates";

describe("dates (R31c)", () => {
  it("formats unambiguously", () => {
    expect(formatDate("2026-11-02")).toBe("Mon 2 Nov 2026");
    expect(formatDate("2026-01-31")).toBe("Sat 31 Jan 2026");
  });
  it("round-trips", () => {
    expect(parseDate(formatDate("2026-11-02"))).toBe("2026-11-02");
    expect(parseDate("2 Nov 2026")).toBe("2026-11-02");
  });
  it("rejects impossible or mismatched dates", () => {
    expect(parseDate("31 Nov 2026")).toBeNull();
    expect(parseDate("Tue 2 Nov 2026")).toBeNull();
    expect(parseDate("11/02/2026")).toBeNull();
    expect(() => formatDate("2026-13-01")).toThrow(RangeError);
  });
  it("uses company timezone for today", () => {
    expect(COMPANY_TZ).toBe("Asia/Ho_Chi_Minh");
    expect(todayIso(new Date("2026-11-01T18:00:00Z"))).toBe("2026-11-02");
  });
});
