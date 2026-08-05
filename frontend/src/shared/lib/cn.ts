type ClassValue = string | false | null | undefined

/** Склейка className с отбрасыванием falsy-значений. */
export function cn(...classes: ClassValue[]): string {
  return classes.filter(Boolean).join(' ')
}
