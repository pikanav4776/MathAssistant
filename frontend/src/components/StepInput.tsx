import type { FormEvent, KeyboardEvent } from "react";

interface StepInputFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder: string;
  disabled?: boolean;
  submitDisabled?: boolean;
  submitLabel: string;
  inputError?: boolean;
  inputErrorMessage?: string;
}

export function StepInputField({
  id,
  label,
  value,
  onChange,
  onSubmit,
  placeholder,
  disabled = false,
  submitDisabled = false,
  submitLabel,
  inputError = false,
  inputErrorMessage = "Please enter an expression.",
}: StepInputFieldProps) {
  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !submitDisabled && !disabled) {
      onSubmit();
    }
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!submitDisabled && !disabled) onSubmit();
  };

  return (
    <form className="input-area" onSubmit={handleSubmit}>
      <label htmlFor={id} className="input-label">
        {label}
      </label>
      <input
        type="text"
        id={id}
        className="step-input"
        placeholder={placeholder}
        autoComplete="off"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
      />
      {inputError ? <p className="inline-error">{inputErrorMessage}</p> : null}
      <button type="submit" className="btn btn-primary" disabled={submitDisabled || disabled}>
        {submitLabel}
      </button>
    </form>
  );
}
