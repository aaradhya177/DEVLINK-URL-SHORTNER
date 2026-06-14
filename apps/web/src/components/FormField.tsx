import type { InputHTMLAttributes, ReactNode } from "react";

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  help?: ReactNode;
}

export function FormField({ label, help, id, ...props }: FormFieldProps) {
  const fieldId = id ?? props.name ?? label;
  return (
    <label className="field" htmlFor={fieldId}>
      <span>{label}</span>
      <input id={fieldId} {...props} />
      {help && <small>{help}</small>}
    </label>
  );
}
