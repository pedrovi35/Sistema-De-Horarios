import { useLayoutEffect, useRef, useState } from "react";

export function formatPhone(value) {
  const digits = value.replace(/\D/g, "").slice(0, 11);
  if (!digits) return "";
  if (digits.length < 2) return `(${digits}`;
  const ddd = `(${digits.slice(0, 2)})`;
  if (digits.length === 2) return ddd;
  const number = digits.slice(2);
  return `${ddd} ${number.slice(0, 5)}${number.length > 5 ? `-${number.slice(5)}` : ""}`;
}

function positionAfterDigits(value, count) {
  if (!count) return value ? 1 : 0;
  let seen = 0;
  for (let index = 0; index < value.length; index += 1) {
    if (/\d/.test(value[index]) && ++seen === count) return index + 1;
  }
  return value.length;
}

export default function PhoneInput({ value, onChange }) {
  const input = useRef(null);
  const [caret, setCaret] = useState(null);

  useLayoutEffect(() => {
    if (caret !== null && document.activeElement === input.current) {
      input.current.setSelectionRange(caret, caret);
    }
  }, [value, caret]);

  function updateValue(rawValue, selectionStart) {
    const digitsBeforeCaret = rawValue.slice(0, selectionStart).replace(/\D/g, "").length;
    const formatted = formatPhone(rawValue);
    onChange(formatted);
    setCaret(positionAfterDigits(formatted, digitsBeforeCaret));
  }

  function handleKeyDown(event) {
    if (event.key !== "Backspace" && event.key !== "Delete") return;
    const { selectionStart, selectionEnd } = event.currentTarget;
    if (selectionStart !== selectionEnd) return;
    // Skip the mask's punctuation so deleting always removes a digit.
    const backwards = event.key === "Backspace";
    let index = backwards ? selectionStart - 1 : selectionStart;
    while (index >= 0 && index < value.length && !/\d/.test(value[index])) {
      index += backwards ? -1 : 1;
    }
    if (index < 0 || index >= value.length) return;
    event.preventDefault();
    const rawValue = value.slice(0, index) + value.slice(index + 1);
    updateValue(rawValue, backwards ? index : selectionStart);
  }

  return (
    <input
      ref={input}
      id="phone"
      type="tel"
      inputMode="numeric"
      autoComplete="tel-national"
      value={value}
      onChange={(event) => updateValue(event.target.value, event.target.selectionStart ?? event.target.value.length)}
      onKeyDown={handleKeyDown}
      pattern="\([0-9]{2}\) [0-9]{5}-[0-9]{4}"
      title="Informe o DDD e o celular completo, por exemplo: (85) 99999-9999"
      required
      placeholder="(85) 99999-9999"
    />
  );
}
