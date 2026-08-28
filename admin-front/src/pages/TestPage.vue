<template>
  <div :class="$style.testPage">
    <h1 :class="$style.title">
      Тесты
    </h1>

    <div :class="$style.actions">
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

<style module>
.testPage {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
}

.title {
  font-size: 1.125rem;
  line-height: 1.75rem;
  font-weight: 600;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
</style>
