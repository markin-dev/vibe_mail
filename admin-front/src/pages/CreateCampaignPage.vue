<template>
  <section
    :class="$style.createCampaignPage"
    data-test="create-campaign-page"
  >
    <div :class="$style.headerRow">
      <h1 :class="$style.title">
        Новая кампания
      </h1>

      <Button
        :disabled="isLoading"
        variant="outline"
        data-test="cancel-button"
        @click="goBack"
      >
        Отмена
      </Button>
    </div>

    <form
      :class="$style.form"
      data-test="create-campaign-form"
      @submit="onSubmit"
    >
      <FormField
        v-slot="{ componentField }"
        name="name"
      >
        <FormItem>
          <FormLabel>Название</FormLabel>

          <FormControl>
            <Input
              id="name"
              :disabled="isLoading"
              data-test="name-input"
              v-bind="componentField"
            />
          </FormControl>

          <FormMessage data-test="name-error" />
        </FormItem>
      </FormField>

      <FormField
        v-slot="{ componentField }"
        name="subject"
      >
        <FormItem>
          <FormLabel>Тема письма</FormLabel>

          <FormControl>
            <Input
              id="subject"
              :disabled="isLoading"
              data-test="subject-input"
              v-bind="componentField"
            />
          </FormControl>

          <FormMessage data-test="subject-error" />
        </FormItem>
      </FormField>

      <FormField
        v-slot="{ componentField }"
        name="body"
      >
        <FormItem>
          <FormLabel>Текст письма</FormLabel>

          <FormControl>
            <Textarea
              id="body"
              :disabled="isLoading"
              data-test="body-input"
              rows="4"
              v-bind="componentField"
            />
          </FormControl>

          <FormMessage data-test="body-error" />
        </FormItem>
      </FormField>

      <Button
        :disabled="isLoading"
        type="submit"
        data-test="submit-button"
      >
        <LoaderCircle
          v-if="isLoading"
          :class="$style.spinner"
        />

        {{ isLoading ? 'Создание…' : 'Создать' }}
      </Button>
    </form>
  </section>
</template>

<script setup lang="ts">
import { toTypedSchema } from '@vee-validate/zod';
import { useForm } from 'vee-validate';
import { useRouter } from 'vue-router';
import { z } from 'zod';

import { LoaderCircle } from '@lucide/vue';
import { Button } from '@/components/ui/button';
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import useCreateCampaign from '@/composables/data/useCreateCampaign';
import useToast from '@/composables/useToast';

const router = useRouter();
const toast = useToast();

const { isLoading, createCampaign, onDone } = useCreateCampaign();

const formSchema = toTypedSchema(
  z.object({
    name: z
      .string({ required_error: 'Это поле обязательно' })
      .min(1, 'Это поле обязательно')
      .max(255, 'Название слишком длинное'),
    subject: z
      .string({ required_error: 'Это поле обязательно' })
      .min(1, 'Это поле обязательно')
      .max(1024, 'Тема слишком длинная'),
    body: z
      .string({ required_error: 'Это поле обязательно' })
      .min(1, 'Это поле обязательно'),
  }),
);

const { handleSubmit } = useForm({ validationSchema: formSchema });

const onSubmit = handleSubmit((values) => {
  createCampaign(values);
});

onDone(() => {
  toast.success('Кампания создана');

  router.push('/campaigns');
});

function goBack() {
  router.push('/campaigns');
}
</script>

<style module>
.createCampaignPage {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 42rem;
}

.headerRow {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  font-size: 1.5rem;
  line-height: 2rem;
  font-weight: 600;
  color: var(--foreground);
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.spinner {
  width: 1rem;
  height: 1rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
