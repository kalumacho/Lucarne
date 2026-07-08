import { readFileSync } from "node:fs";
import { join } from "node:path";

export type Consultation = {
  title: string;
  category: string | null;
  opened_at: string | null;
  closes_at: string | null;
  days_left: number | null;
  contributions: number;
  url: string;
  source: string | null;
  digest: string;
};

export type Urgency = "critique" | "proche" | "ouverte";

export function urgency(daysLeft: number | null): Urgency {
  if (daysLeft === null) return "ouverte";
  if (daysLeft <= 3) return "critique";
  if (daysLeft <= 10) return "proche";
  return "ouverte";
}

export function joursLabel(daysLeft: number | null): string {
  if (daysLeft === null) return "date à confirmer";
  if (daysLeft <= 0) return "ferme aujourd’hui";
  if (daysLeft === 1) return "ferme demain";
  return `ferme dans ${daysLeft} jours`;
}

const FR_DATE = new Intl.DateTimeFormat("fr-FR", {
  day: "numeric",
  month: "long",
  year: "numeric",
});

export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return FR_DATE.format(new Date(iso));
}

export function loadConsultations(): Consultation[] {
  const path = join(process.cwd(), "data", "digests.json");
  const data = JSON.parse(readFileSync(path, "utf-8")) as Consultation[];
  // Tri par urgence : clôtures les plus proches d'abord, dates inconnues en fin.
  return data.sort((a, b) => {
    if (a.days_left === null) return 1;
    if (b.days_left === null) return -1;
    return a.days_left - b.days_left;
  });
}
