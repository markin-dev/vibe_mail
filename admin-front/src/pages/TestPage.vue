<template>
  <div class="flex flex-col gap-4 p-4">
    <h1 class="text-lg font-semibold">
      Тесты
    </h1>

    <div class="flex flex-wrap gap-2">
      <Button
        data-test="toast-success"
        variant="default"
        @click="onSuccess"
      >
        Успех
      </Button>

      <Button
        data-test="toast-error"
        variant="destructive"
        @click="onError"
      >
        Ошибка
      </Button>

      <Button
        data-test="toast-info"
        variant="outline"
        @click="onInfo"
      >
        Инфо
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button';
import useToast from '@/composables/useToast';

const { success, error, info } = useToast();

function onSuccess() {
  success();
}

function onError() {
  error();
}

function onInfo() {
  info();
}
</script>
