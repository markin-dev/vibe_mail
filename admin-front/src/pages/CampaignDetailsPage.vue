<template>
  <section
    data-test="campaign-details-page"
    class="flex flex-col gap-6"
  >
    <div class="flex items-start justify-between gap-4">
      <div class="flex items-center gap-3">
        <Button
          variant="outline"
          size="icon"
          data-test="back-button"
          @click="goBack"
        >
          <ArrowLeft class="h-4 w-4" />
        </Button>

        <div
          v-if="campaign"
          class="flex items-center gap-3"
        >
          <h1 class="text-2xl font-semibold text-foreground">
            {{ campaign.name }}
          </h1>

          <Badge :class="statusClass(campaign.status)">
            {{ statusLabel(campaign.status) }}
          </Badge>
        </div>

        <Skeleton
          v-else-if="isLoadingCampaign"
          class="h-8 w-64"
        />
      </div>

      <Button
        :disabled="isStarting || campaign?.status === 'in_progress'"
        data-test="start-button"
        @click="onStart"
      >
        <LoaderCircle
          v-if="isStarting"
          class="h-4 w-4 animate-spin"
        />

        {{ isStarting ? 'Запуск…' : 'Запустить рассылку' }}
      </Button>
    </div>

    <div
      v-if="campaign"
      data-test="campaign-info"
      class="
        grid gap-4 rounded-md border p-4
        sm:grid-cols-2
      "
    >
      <div>
        <p class="text-sm text-muted-foreground">
          Тема
        </p>

        <p class="font-medium">
          {{ campaign.subject }}
        </p>
      </div>

      <div>
        <p class="text-sm text-muted-foreground">
          Создана
        </p>

        <p class="font-medium">
          {{ formatDate(campaign.createdAt) }}
        </p>
      </div>

      <div class="sm:col-span-2">
        <p class="text-sm text-muted-foreground">
          Текст письма
        </p>

        <p class="whitespace-pre-wrap font-medium">
          {{ campaign.body }}
        </p>
      </div>

      <div
        v-if="campaign.totals"
        class="sm:col-span-2"
      >
        <p class="text-sm text-muted-foreground">
          Прогресс
        </p>

        <p class="font-medium">
          Отправлено: {{ campaign.totals.sent }} /
          Всего: {{ campaign.totals.total }} /
          Ошибки: {{ campaign.totals.failed }} /
          Ожидают: {{ campaign.totals.pending }}
        </p>
      </div>
    </div>

    <div
      data-test="recipients-log"
      class="rounded-md border"
    >
      <div class="border-b p-4">
        <h2 class="text-lg font-semibold">
          Лог отправленных писем
        </h2>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Email</TableHead>
            <TableHead>Имя</TableHead>
            <TableHead>Статус</TableHead>
            <TableHead>Ошибка</TableHead>
            <TableHead>Отправлено</TableHead>
            <TableHead>Вложения</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          <template v-if="isLoadingRecipients">
            <TableRow
              v-for="n in 3"
              :key="n"
              data-test="recipient-skeleton-row"
            >
              <TableCell><Skeleton class="h-4 w-40" /></TableCell>
              <TableCell><Skeleton class="h-4 w-32" /></TableCell>
              <TableCell><Skeleton class="h-5 w-20 rounded-full" /></TableCell>
              <TableCell><Skeleton class="h-4 w-24" /></TableCell>
              <TableCell><Skeleton class="h-4 w-24" /></TableCell>
              <TableCell><Skeleton class="h-4 w-12" /></TableCell>
            </TableRow>
          </template>

          <template v-else>
            <TableEmpty
              v-if="recipientsList.length === 0"
              :colspan="6"
            >
              Получатели не найдены
            </TableEmpty>

            <TableRow
              v-for="recipient in recipientsList"
              v-else
              :key="recipient.id"
              data-test="recipient-row"
            >
              <TableCell>{{ recipient.email }}</TableCell>
              <TableCell>{{ recipient.name ?? '—' }}</TableCell>

              <TableCell>
                <Badge :class="recipientStatusClass(recipient.status)">
                  {{ recipientStatusLabel(recipient.status) }}
                </Badge>
              </TableCell>

              <TableCell class="text-destructive">
                {{ recipient.error ?? '—' }}
              </TableCell>

              <TableCell>
                {{ recipient.sentAt ? formatDate(recipient.sentAt) : '—' }}
              </TableCell>

              <TableCell>{{ recipient.attachments.length }}</TableCell>
            </TableRow>
          </template>
        </TableBody>
      </Table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { ArrowLeft, LoaderCircle } from '@lucide/vue';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableEmpty,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import useGetCampaign from '@/composables/data/useGetCampaign';
import useGetRecipients from '@/composables/data/useGetRecipients';
import useStartCampaign from '@/composables/data/useStartCampaign';
import useToast from '@/composables/useToast';
import type { CampaignStatus } from '@/apiService/campaigns/campaignsApiTypes';
import type { RecipientStatus } from '@/apiService/recipients/recipientsApiTypes';

const route = useRoute();
const router = useRouter();
const toast = useToast();

const campaignId = computed(() => Number(route.params.id));

const {
  isLoading: isLoadingCampaign,
  campaign,
  getCampaign,
} = useGetCampaign();

const {
  isLoading: isLoadingRecipients,
  recipients,
  getRecipients,
} = useGetRecipients();

const {
  isLoading: isStarting,
  startCampaign,
  onDone,
} = useStartCampaign();

const recipientsList = computed(() => recipients.value ?? []);

const POLL_INTERVAL = 3000;
let pollTimer: number | undefined;
let pollInFlight = false;

function load(): Promise<void> {
  const id = campaignId.value;

  return Promise.all([
    getCampaign({ id }),
    getRecipients({ campaignId: id }),
  ])
    .then(() => undefined)
    .catch(() => undefined);
}

function pollOnce() {
  if (pollInFlight) {
    return;
  }

  pollInFlight = true;
  load().finally(() => {
    pollInFlight = false;
  });
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(pollOnce, POLL_INTERVAL);
}

function stopPolling() {
  if (pollTimer !== undefined) {
    clearInterval(pollTimer);
    pollTimer = undefined;
  }
}

function onStart() {
  if (!campaign.value) {
    return;
  }

  startCampaign({ id: campaign.value.id });
}

onDone(() => {
  toast.success('Рассылка запущена');

  load();
});

watch(
  () => campaign.value?.status,
  (status) => {
    if (status === 'in_progress') {
      startPolling();
    } else {
      stopPolling();
    }
  },
  { immediate: true },
);

onMounted(load);
onUnmounted(stopPolling);

function goBack() {
  router.push('/campaigns');
}

const STATUS_LABEL: Record<CampaignStatus, string> = {
  new: 'Новая',
  in_progress: 'В работе',
  done: 'Завершена',
  error: 'Ошибка',
};

const STATUS_CLASS: Record<CampaignStatus, string> = {
  new: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  in_progress: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300',
  done: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  error: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
};

function statusLabel(status: CampaignStatus): string {
  return STATUS_LABEL[status];
}

function statusClass(status: CampaignStatus): string {
  return STATUS_CLASS[status];
}

const RECIPIENT_STATUS_LABEL: Record<RecipientStatus, string> = {
  pending: 'Ожидает',
  sent: 'Отправлено',
  failed: 'Ошибка',
  skipped: 'Пропущено',
};

const RECIPIENT_STATUS_CLASS: Record<RecipientStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300',
  sent: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  failed: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  skipped: 'bg-gray-100 text-gray-700 dark:bg-gray-900/40 dark:text-gray-300',
};

function recipientStatusLabel(status: RecipientStatus): string {
  return RECIPIENT_STATUS_LABEL[status];
}

function recipientStatusClass(status: RecipientStatus): string {
  return RECIPIENT_STATUS_CLASS[status];
}

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}
</script>
