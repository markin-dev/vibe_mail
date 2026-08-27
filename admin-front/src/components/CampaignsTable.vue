<template>
  <div
    data-test="campaigns-table"
    class="rounded-md border"
  >
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>ID</TableHead>
          <TableHead>Название</TableHead>
          <TableHead>Тема</TableHead>
          <TableHead>Статус</TableHead>
          <TableHead>Прогресс</TableHead>
          <TableHead>Создана</TableHead>
        </TableRow>
      </TableHeader>

      <TableBody>
        <template v-if="props.isLoading">
          <TableRow
            v-for="n in 5"
            :key="n"
            data-test="campaign-skeleton-row"
          >
            <TableCell><Skeleton class="h-4 w-8" /></TableCell>
            <TableCell><Skeleton class="h-4 w-40" /></TableCell>
            <TableCell><Skeleton class="h-4 w-48" /></TableCell>
            <TableCell><Skeleton class="h-5 w-20 rounded-full" /></TableCell>
            <TableCell><Skeleton class="h-4 w-16" /></TableCell>
            <TableCell><Skeleton class="h-4 w-24" /></TableCell>
          </TableRow>
        </template>

        <template v-else>
          <TableEmpty
            v-if="props.campaigns.length === 0"
            :colspan="6"
          >
            Кампании не найдены
          </TableEmpty>

          <TableRow
            v-for="campaign in props.campaigns"
            v-else
            :key="campaign.id"
            data-test="campaign-row"
          >
            <TableCell>{{ campaign.id }}</TableCell>

            <TableCell class="font-medium">
              {{ campaign.name }}
            </TableCell>

            <TableCell>{{ campaign.subject }}</TableCell>

            <TableCell>
              <Badge :class="statusClass(campaign.status)">
                {{ statusLabel(campaign.status) }}
              </Badge>
            </TableCell>

            <TableCell>
              <span v-if="campaign.totals">
                {{ campaign.totals.sent }} / {{ campaign.totals.total }}
              </span>

              <span v-else>—</span>
            </TableCell>

            <TableCell>{{ formatDate(campaign.createdAt) }}</TableCell>
          </TableRow>
        </template>
      </TableBody>
    </Table>
  </div>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge';
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
import type { Campaign, CampaignStatus } from '@/apiService/campaigns/campaignsApiTypes';

interface Props {
  campaigns?: Campaign[];
  isLoading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  campaigns: () => [],
  isLoading: false,
});

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
