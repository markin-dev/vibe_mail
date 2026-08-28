<template>
  <Dialog v-model:open="isOpen">
    <DialogContent
      :class="$style.dialogContent"
      data-test="add-recipients-dialog"
    >
      <DialogHeader>
        <DialogTitle>Добавить получателей</DialogTitle>

        <DialogDescription>
          Вставьте две колонки из таблицы: имя конфига и почта. Строки с одинаковой
          почтой уедут одним письмом.
        </DialogDescription>
      </DialogHeader>

      <div
        v-if="isInputStep"
        :class="$style.step"
        data-test="input-step"
      >
        <Textarea
          v-model="text"
          :class="$style.textarea"
          placeholder="Markin_Sergey&#9;shpenator@gmail.com"
          data-test="recipients-textarea"
        />
      </div>

      <div
        v-else-if="preview"
        :class="$style.step"
        data-test="preview-step"
      >
        <p
          :class="$style.summary"
          data-test="preview-summary"
        >
          {{ preview.totalRows }} {{ rowsLabel }} → {{ preview.groups.length }} {{ lettersLabel }},
          конфигов {{ preview.totalConfigs }}
        </p>

        <div
          v-if="preview.problems.length"
          :class="$style.problems"
          data-test="preview-problems"
        >
          <p :class="$style.problemsTitle">
            Не добавим {{ preview.problems.length }} {{ problemsLabel }}:
          </p>

          <p
            v-for="problem in preview.problems"
            :key="problem.line"
            :class="$style.problem"
            data-test="preview-problem"
          >
            Строка {{ problem.line }}: {{ problem.raw || '—' }} — {{ problem.reason }}
          </p>
        </div>

        <div :class="$style.groups">
          <div
            v-for="group in preview.groups"
            :key="group.email"
            :class="$style.group"
            data-test="preview-group"
          >
            <div :class="$style.groupHeader">
              <span :class="$style.email">{{ group.email }}</span>

              <Badge
                v-if="group.isExisting"
                :class="$style.existingBadge"
                data-test="existing-badge"
              >
                уже в кампании
              </Badge>

              <span :class="$style.count">
                {{ group.configs.length }} {{ configsLabel(group.configs.length) }}
              </span>
            </div>

            <div :class="$style.chips">
              <span
                v-for="config in group.existingConfigs"
                :key="`existing-${config}`"
                :class="[$style.chip, $style.chipExisting]"
                data-test="existing-config-chip"
              >
                {{ config }}
              </span>

              <span
                v-for="config in group.configs"
                :key="config"
                :class="$style.chip"
                data-test="config-chip"
              >
                {{ config }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <DialogFooter>
        <Button
          v-if="isInputStep"
          :disabled="isPreviewDisabled"
          data-test="parse-button"
          @click="onParse"
        >
          <LoaderCircle
            v-if="isPreviewLoading"
            :class="$style.spinner"
          />

          Разобрать
        </Button>

        <template v-else>
          <Button
            :disabled="isImporting"
            variant="outline"
            data-test="back-button"
            @click="goBack"
          >
            Назад
          </Button>

          <Button
            :disabled="isImportDisabled"
            data-test="import-button"
            @click="onImport"
          >
            <LoaderCircle
              v-if="isImporting"
              :class="$style.spinner"
            />

            {{ importLabel }}
          </Button>
        </template>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import { LoaderCircle } from '@lucide/vue';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import useImportRecipients from '@/composables/data/useImportRecipients';
import usePreviewRecipientsImport from '@/composables/data/usePreviewRecipientsImport';
import useToast from '@/composables/useToast';

interface Props {
  campaignId: number;
}

const props = defineProps<Props>();

const emit = defineEmits<{ added: [] }>();

const isOpen = defineModel<boolean>('open', { default: false });

const toast = useToast();

const {
  isLoading: isPreviewLoading,
  preview,
  previewRecipientsImport,
  onDone: onPreviewDone,
} = usePreviewRecipientsImport();

const {
  isLoading: isImporting,
  importResult,
  importRecipients,
  onDone: onImportDone,
} = useImportRecipients();

const text = ref('');
const isInputStep = ref(true);

const isPreviewDisabled = computed(() => isPreviewLoading.value || !text.value.trim());

const isImportDisabled = computed(
  () => isImporting.value || !preview.value || preview.value.groups.length === 0,
);

function plural(count: number, one: string, few: string, many: string): string {
  const mod100 = count % 100;

  if (mod100 >= 11 && mod100 <= 14) {
    return many;
  }

  const mod10 = count % 10;

  if (mod10 === 1) {
    return one;
  }

  if (mod10 >= 2 && mod10 <= 4) {
    return few;
  }

  return many;
}

const rowsLabel = computed(() => plural(preview.value?.totalRows ?? 0, 'строка', 'строки', 'строк'));

const lettersLabel = computed(
  () => plural(preview.value?.groups.length ?? 0, 'письмо', 'письма', 'писем'),
);

const problemsLabel = computed(
  () => plural(preview.value?.problems.length ?? 0, 'строку', 'строки', 'строк'),
);

function configsLabel(count: number): string {
  return plural(count, 'конфиг', 'конфига', 'конфигов');
}

const importLabel = computed(() => {
  const groups = preview.value?.groups ?? [];
  const newCount = groups.filter((group) => !group.isExisting).length;
  const existingCount = groups.length - newCount;

  const parts: string[] = [];

  if (newCount) {
    parts.push(`Добавить ${newCount} ${plural(newCount, 'получателя', 'получателей', 'получателей')}`);
  }

  if (existingCount) {
    parts.push(`дополнить ${existingCount}`);
  }

  return parts.length ? parts.join(' и ') : 'Добавить';
});

function onParse() {
  previewRecipientsImport({ campaignId: props.campaignId, text: text.value });
}

onPreviewDone(() => {
  isInputStep.value = false;
});

function goBack() {
  isInputStep.value = true;
}

function onImport() {
  importRecipients({ campaignId: props.campaignId, text: text.value });
}

onImportDone(() => {
  const result = importResult.value;

  if (!result) {
    return;
  }

  const added = result.createdRecipients + result.updatedRecipients;
  const skipped = result.problems.length;

  toast.success(
    skipped
      ? `Добавлено ${added}, пропущено ${skipped}`
      : `Добавлено ${added}`,
  );

  emit('added');

  isOpen.value = false;
});

watch(isOpen, (opened) => {
  if (!opened) {
    text.value = '';
    isInputStep.value = true;
  }
});
</script>

<style module>
.dialogContent {
  max-width: 46rem;
}

.step {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 60vh;
  overflow-y: auto;
}

.textarea {
  min-height: 14rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.summary {
  font-weight: 600;
  color: var(--foreground);
}

.problems {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  border: 1px solid var(--destructive);
  border-radius: var(--radius-md);
  padding: 0.75rem;
}

.problemsTitle {
  font-weight: 500;
  color: var(--destructive);
}

.problem {
  color: var(--muted-foreground);
  overflow-wrap: anywhere;
}

.groups {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 0.75rem;
}

.groupHeader {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.email {
  font-weight: 500;
  overflow-wrap: anywhere;
}

.count {
  margin-left: auto;
  white-space: nowrap;
  color: var(--muted-foreground);
}

.existingBadge {
  background-color: #dbeafe;
  color: #1d4ed8;
}

:global(.dark) .existingBadge {
  background-color: rgba(30, 58, 138, 0.4);
  color: #93c5fd;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.chip {
  border: 1px solid var(--border);
  border-radius: 9999px;
  padding: 0.125rem 0.5rem;
  overflow-wrap: anywhere;
}

.chipExisting {
  color: var(--muted-foreground);
  border-style: dashed;
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
