<template>
  <section
    data-test="create-campaign-page"
    class="flex flex-col gap-6 max-w-2xl"
  >
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold text-foreground">
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
      data-test="create-campaign-form"
      class="flex flex-col gap-4"
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
          class="h-4 w-4 animate-spin"
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
