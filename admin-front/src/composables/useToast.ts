import { toast } from 'vue-sonner'

export const DEFAULT_SUCCESS_TEXT = 'Операция успешна';
export const DEFAULT_INFO_TEXT = 'Информация';
export const DEFAULT_ERROR_TEXT = 'Что-то пошло не так';

export default function useToast() {
  function success(text?: string) {
    toast.success(text || DEFAULT_SUCCESS_TEXT);
  }

  function info(text?: string) {
    toast.info(text || DEFAULT_INFO_TEXT);
  }

  function error(text?: string) {
    toast.error(text || DEFAULT_ERROR_TEXT);
  }

  return {
    success,
    info,
    error,
  };
}
