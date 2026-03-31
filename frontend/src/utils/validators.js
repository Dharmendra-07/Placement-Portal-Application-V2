/**
 * utils/validators.js
 * Frontend validation helpers. Each validator returns { valid, message }.
 */
export const v = {
  required:   (val, label = "This field") => ({
    valid:   val !== null && val !== undefined && String(val).trim() !== "",
    message: `${label} is required.`,
  }),
  email: (val) => ({
    valid:   /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(val || "").trim()),
    message: "Enter a valid email address.",
  }),
  minLength: (val, min, label = "This field") => ({
    valid:   String(val || "").trim().length >= min,
    message: `${label} must be at least ${min} characters.`,
  }),
  maxLength: (val, max, label = "This field") => ({
    valid:   String(val || "").trim().length <= max,
    message: `${label} must be ${max} characters or fewer.`,
  }),
  numeric:   (val, label = "This field") => ({
    valid:   !isNaN(parseFloat(val)) && isFinite(val),
    message: `${label} must be a number.`,
  }),
  range:     (val, min, max, label = "This field") => ({
    valid:   parseFloat(val) >= min && parseFloat(val) <= max,
    message: `${label} must be between ${min} and ${max}.`,
  }),
  cgpa: (val) => ({
    valid:   !val || (parseFloat(val) >= 0 && parseFloat(val) <= 10),
    message: "CGPA must be between 0.0 and 10.0.",
  }),
  phone: (val) => ({
    valid:   !val || /^[+\d\s\-()\[\]]{7,15}$/.test(String(val).trim()),
    message: "Enter a valid phone number.",
  }),
  url: (val) => ({
    valid:   !val || /^https?:\/\/.+\..+/.test(String(val).trim()),
    message: "Enter a valid URL (https://...).",
  }),
  futureDate: (val, label = "Date") => ({
    valid:   !val || new Date(val) > new Date(),
    message: `${label} must be in the future.`,
  }),
}

/**
 * Run multiple validators against a form object.
 * @param {Object} form  - reactive form data
 * @param {Object} rules - { field: [[validatorFn, ...args], ...] }
 * @returns { errors: {field: msg}, valid: bool }
 */
export function validate(form, rules) {
  const errors = {}
  let   allValid = true
  for (const [field, checks] of Object.entries(rules)) {
    const value = form[field]
    for (const [fn, ...args] of checks) {
      const result = fn(value, ...args)
      if (!result.valid) {
        errors[field] = result.message
        allValid      = false
        break
      }
    }
  }
  return { errors, valid: allValid }
}
