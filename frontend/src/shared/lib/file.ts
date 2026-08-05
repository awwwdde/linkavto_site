/** Предел размера аватара: 2 МБ — дальше data-URL слишком тяжёл для профиля. */
export const MAX_AVATAR_BYTES = 2 * 1024 * 1024

/**
 * Читает выбранное изображение как data-URL.
 *
 * Аватар хранится строкой (мок-API не принимает multipart), поэтому файл
 * кодируется на клиенте и уходит вместе с остальными полями аккаунта.
 */
export function readImageAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result
      if (typeof result === 'string') resolve(result)
      else reject(new Error('Не удалось прочитать файл'))
    }
    reader.onerror = () => reject(reader.error ?? new Error('Не удалось прочитать файл'))
    reader.readAsDataURL(file)
  })
}
