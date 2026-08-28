<template>
  <section
    :class="$style.campaignDetailsPage"
    data-test="campaign-details-page"
  >
    <div :class="$style.headerRow">
      <div :class="$style.titleGroup">
        <Button
          variant="outline"
          size="icon"
          data-test="back-button"
          @click="goBack"
        >
          <ArrowLeft :class="$style.iconBtn" />
        </Button>

        <div
          v-if="campaign"
          :class="$style.titleGroup"
        >
          <h1 :class="$style.title">
            {{ campaign.name }}
          </h1>

          <Badge :class="statusClass(currentStatus)">
            {{ statusLabel(currentStatus) }}
          </Badge>
        </div>

        <Skeleton
          v-else-if="isLoadingCampaign"
          :class="$style.skTitle"
        />
      </div>

      <div :class="$style.actions">
        <Button
          :disabled="isAddRecipientsDisabled"
          variant="outline"
          data-test="add-recipients-button"
          @click="openAddRecipients"
        >
          Добавить получателей
        </Button>

        <Button
          :disabled="isButtonDisabled"
          data-test="start-button"
          @click="onStart"
        >
          <LoaderCircle
            v-if="isButtonLoading"
            :class="$style.spinner"
          />

          {{ buttonLabel }}
        </Button>
      </div>
    </div>

    <div
      v-if="campaign"
      :class="$style.infoCard"
      data-test="campaign-info"
    >
      <div>
        <p :class="$style.label">
          Тема
        </p>

        <p :class="$style.value">
          {{ campaign.subject }}
        </p>
      </div>

      <div>
        <p :class="$style.label">
          Создана
        </p>

        <p :class="$style.value">
          {{ formatDate(campaign.createdAt) }}
        </p>
      </div>

      <div :class="$style.fullWidth">
        <p :class="$style.label">
          Текст письма
        </p>

        <p :class="$style.body">
          {{ campaign.body }}
        </p>
      </div>

      <div :class="$style.fullWidth">
        <p :class="$style.label">
          Прогресс
        </p>

        <p :class="$style.value">
          Отправлено: {{ progressTotals.sent }} /
          Всего: {{ progressTotals.total }} /
          Ошибки: {{ progressTotals.failed }} /
          Ожидают: {{ progressTotals.pending }}
        </p>
      </div>
    </div>

    <div
      :class="$style.logCard"
      data-test="recipients-log"
    >
      <div :class="$style.logHeader">
        <h2 :class="$style.logTitle">
          Лог отправленных писем
        </h2>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Email</TableHead>
            <TableHead>Имя</TableHead>

            <TableHead :class="$style.colStatus">
              Статус
            </TableHead>

            <TableHead :class="$style.colError">
              Ошибка
            </TableHead>

            <TableHead>Отправлено</TableHead>
            <TableHead>Конфиги</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          <template v-if="isInitRecipientsLoading">
            <TableRow
              v-for="n in 3"
              :key="n"
              data-test="recipient-skeleton-row"
            >
              <TableCell><Skeleton :class="$style.skEmail" /></TableCell>
              <TableCell><Skeleton :class="$style.skName" /></TableCell>
              <TableCell><Skeleton :class="$style.skStatus" /></TableCell>
              <TableCell><Skeleton :class="$style.skError" /></TableCell>
              <TableCell><Skeleton :class="$style.skSent" /></TableCell>
              <TableCell><Skeleton :class="$style.skConfigs" /></TableCell>
            </TableRow>
          </template>

          <template v-else>
            <TableEmpty
              v-if="recipientsList.length === 0"
              :colspan="6"
            >
              Получателей пока нет — добавьте их, вставив список из таблицы
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

              <TableCell :class="$style.cellError">
                <TooltipProvider v-if="recipient.error">
                  <Tooltip>
                    <TooltipTrigger as-child>
                      <span :class="$style.errorText">
                        {{ recipient.error }}
                      </span>
                    </TooltipTrigger>

                    <TooltipContent>
                      <p :class="$style.tooltipText">
                        {{ recipient.error }}
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                <span
                  v-else
                  :class="$style.errorEmpty"
                >—</span>
              </TableCell>

              <TableCell>
                {{ recipient.sentAt ? formatDate(recipient.sentAt) : '—' }}
              </TableCell>

              <TableCell>
                <span
                  v-for="config in recipient.configs"
                  :key="config.id"
                  :class="$style.configName"
                  data-test="recipient-config"
                >
                  {{ config.name }}
                </span>

                <span v-if="recipient.configs.length === 0">—</span>
              </TableCell>
            </TableRow>
          </template>
        </TableBody>
      </Table>
    </div>

    <AddRecipientsDialog
      v-model:open="isAddRecipientsOpen"
      :campaign-id="campaignId"
      @added="load"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch, useCssModule } from 'vue';
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import AddRecipientsDialog from '@/components/AddRecipientsDialog.vue';
import useGetCampaign from '@/composables/data/useGetCampaign';
import useGetRecipients from '@/composables/data/useGetRecipients';
import useStartCampaign from '@/composables/data/useStartCampaign';
import useToast from '@/composables/useToast';
import type { CampaignStatus } from '@/apiService/campaigns/campaignsApiTypes';
import type { RecipientStatus } from '@/apiService/recipients/recipientsApiTypes';

const styles = useCssModule();

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
  recipients,
  getRecipients,
  onDone: onRecipientsDone,
  onError: onRecipientsError,
} = useGetRecipients();

const isInitRecipientsLoading = ref(true);
onRecipientsDone(() => {
  isInitRecipientsLoading.value = false;
});
onRecipientsError(() => {
  isInitRecipientsLoading.value = false;
});

const {
  startCampaign,
  onDone,
} = useStartCampaign();

const recipientsList = computed(() => recipients.value ?? []);

const progressTotals = computed(() => {
  const list = recipientsList.value;

  return {
    sent: list.filter((recipient) => recipient.status === 'sent').length,
    failed: list.filter((recipient) => recipient.status === 'failed').length,
    pending: list.filter((recipient) => recipient.status === 'pending').length,
    total: list.length,
  };
});

const effectiveStatus = computed(() => campaign.value?.status);
const currentStatus = computed<CampaignStatus>(() => effectiveStatus.value ?? 'new');

const DISABLED_STATUSES: CampaignStatus[] = ['in_progress', 'done', 'done_with_errors', 'error'];

const isCampaignStarted = ref(false);

const isAddRecipientsOpen = ref(false);

const isAddRecipientsDisabled = computed(() => currentStatus.value !== 'new');

function openAddRecipients() {
  isAddRecipientsOpen.value = true;
}

const isCompleted = computed(() => DISABLED_STATUSES.includes(currentStatus.value));

const isButtonLoading = computed(
  () => isCampaignStarted.value || currentStatus.value === 'in_progress',
);

const isButtonDisabled = computed(
  () => isCampaignStarted.value || isCompleted.value,
);

const buttonLabel = computed(() => {
  if (isButtonLoading.value) {
    return 'Рассылка запущена';
  }

  if (isButtonDisabled.value) {
    return 'Рассылка завершена';
  }

  return 'Запустить рассылку';
});

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
  Promise.all([
    getCampaign({ id: campaignId.value }),
    getRecipients({ campaignId: campaignId.value }),
  ])
    .then(() => undefined)
    .catch(() => undefined)
    .finally(() => {
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

  isCampaignStarted.value = true;

  load();
});

watch(
  effectiveStatus,
  (status) => {
    if (status === 'in_progress') {
      startPolling();
      return;
    }

    const wasPolling = pollTimer !== undefined;
    stopPolling();
    if (wasPolling) {
      Promise.all([
        getCampaign({ id: campaignId.value }),
        getRecipients({ campaignId: campaignId.value }),
      ]);
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
  done_with_errors: 'Завершена с ошибками',
  error: 'Ошибка',
};

const STATUS_CLASS: Record<CampaignStatus, string> = {
  new: styles.statusNew,
  in_progress: styles.statusInProgress,
  done: styles.statusDone,
  done_with_errors: styles.statusDoneWithErrors,
  error: styles.statusError,
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
};

const RECIPIENT_STATUS_CLASS: Record<RecipientStatus, string> = {
  pending: styles.recPending,
  sent: styles.recSent,
  failed: styles.recFailed,
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

<style module>
.campaignDetailsPage {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.headerRow {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.titleGroup {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.title {
  font-size: 1.5rem;
  line-height: 2rem;
  font-weight: 600;
  color: var(--foreground);
}

.actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.skTitle {
  height: 2rem;
  width: 16rem;
}

.infoCard {
  display: grid;
  gap: 1rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1rem;
}

@media (min-width: 640px) {
  .infoCard {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.label {
  font-size: 0.875rem;
  line-height: 1.25rem;
  color: var(--muted-foreground);
}

.value {
  font-weight: 500;
}

.body {
  white-space: pre-wrap;
  font-weight: 500;
}

.fullWidth {
  grid-column: span 2 / span 2;
}

.logCard {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.logHeader {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-bottom: 1px solid var(--border);
  padding: 1rem;
}

.logTitle {
  font-size: 1.125rem;
  line-height: 1.75rem;
  font-weight: 600;
}

.colStatus {
  width: 6.25rem;
}

.colError {
  width: 50rem;
  max-width: 50rem;
}

.cellError {
  width: 50rem;
  max-width: 50rem;
}

.errorText {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--destructive);
}

.errorEmpty {
  color: var(--destructive);
}

.tooltipText {
  max-width: 20rem;
  overflow-wrap: break-word;
}

.iconBtn {
  width: 1rem;
  height: 1rem;
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

.skEmail {
  height: 1rem;
  width: 10rem;
}

.skName {
  height: 1rem;
  width: 8rem;
}

.skStatus {
  height: 1.25rem;
  width: 5rem;
  border-radius: 9999px;
}

.skError {
  height: 1rem;
  width: 6rem;
}

.skSent {
  height: 1rem;
  width: 6rem;
}

.skConfigs {
  height: 1rem;
  width: 8rem;
}

.configName {
  display: block;
  overflow-wrap: anywhere;
}

.statusNew {
  background-color: #dbeafe;
  color: #1d4ed8;
}

.statusInProgress {
  background-color: #fef9c3;
  color: #854d0e;
}

.statusDone {
  background-color: #dcfce7;
  color: #15803d;
}

.statusDoneWithErrors,
.statusError {
  background-color: #fee2e2;
  color: #b91c1c;
}

:global(.dark) .statusNew {
  background-color: rgba(30, 58, 138, 0.4);
  color: #93c5fd;
}

:global(.dark) .statusInProgress {
  background-color: rgba(113, 63, 18, 0.4);
  color: #fde047;
}

:global(.dark) .statusDone {
  background-color: rgba(20, 83, 45, 0.4);
  color: #86efac;
}

:global(.dark) .statusDoneWithErrors,
:global(.dark) .statusError {
  background-color: rgba(127, 29, 29, 0.4);
  color: #fca5a5;
}

.recPending {
  background-color: #fef9c3;
  color: #854d0e;
}

.recSent {
  background-color: #dcfce7;
  color: #15803d;
}

.recFailed {
  background-color: #fee2e2;
  color: #b91c1c;
}

:global(.dark) .recPending {
  background-color: rgba(113, 63, 18, 0.4);
  color: #fde047;
}

:global(.dark) .recSent {
  background-color: rgba(20, 83, 45, 0.4);
  color: #86efac;
}

:global(.dark) .recFailed {
  background-color: rgba(127, 29, 29, 0.4);
  color: #fca5a5;
}
</style>
