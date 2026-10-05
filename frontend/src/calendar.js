export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function getCalendarDownloadUrl(appointment) {
  const params = new URLSearchParams({
    date: appointment.date,
    time: appointment.time.slice(0, 5),
  });
  return `${API_URL.replace(/\/$/, "")}/calendar.ics?${params}`;
}
