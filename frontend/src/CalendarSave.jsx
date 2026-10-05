import { useEffect, useState } from "react";
import QRCode from "qrcode";
import { getCalendarDownloadUrl } from "./calendar.js";

export default function CalendarSave({ appointment }) {
  const calendarUrl = getCalendarDownloadUrl(appointment);
  const [qr, setQr] = useState(null);
  const [qrError, setQrError] = useState(false);

  useEffect(() => {
    let active = true;
    setQr(null);
    setQrError(false);
    QRCode.toDataURL(calendarUrl, {
      width: 360,
      margin: 4,
      errorCorrectionLevel: "M",
      color: { dark: "#174b3e", light: "#ffffff" },
    }).then((data) => { if (active) setQr(data); })
      .catch(() => { if (active) setQrError(true); });
    return () => { active = false; };
  }, [calendarUrl]);

  return (
    <div className="calendar-save">
      <div className="calendar-qr">
        {qr ? <img src={qr} width="120" height="120" alt="QR code para salvar esta consulta na agenda do celular" />
          : <span className="qr-placeholder">{qrError ? "QR indisponível" : "Gerando QR…"}</span>}
        <span>Clínica Bem-Estar</span>
      </div>
      <div className="calendar-copy">
        <h2>Salve na agenda do seu celular</h2>
        <p>{qrError ? "Não foi possível gerar o QR code. Sua consulta continua confirmada."
          : "Sua consulta já está marcada. Leia o QR code para guardar a data e o horário na sua agenda."}</p>
      </div>
    </div>
  );
}
