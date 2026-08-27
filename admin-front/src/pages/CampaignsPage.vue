<template>
  <section
    data-test="campaigns-page"
    class="flex flex-col gap-4"
  >
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold text-foreground">
        Кампании
      </h1>

      <Button
        :disabled="isLoading"
        data-test="refresh-button"
        variant="outline"
        @click="load"
      >
        Обновить
      </Button>
    </div>

    <p class="text-muted-foreground">
      Список кампаний и управление рассылками.
    </p>

    <div
      data-test="campaigns-table"
      class="rounded-md border"
    >
      <Table>
        <TableCaption>
          Всего кампаний: {{ campaigns.length }}
        </TableCaption>

        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>Название</TableHead>
            <TableHead>Тема</TableHead>
            <TableHead>Отправитель</TableHead>
            <TableHead>Статус</TableHead>
            <TableHead>Прогресс</TableHead>
            <TableHead>Создана</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          <TableEmpty
            v-if="campaigns.length === 0"
            :colspan="7"
          >
            <template v-if="isLoading">
              Загрузка…
            </template>

            <template v-else-if="error">
              {{ error }}
            </template>

            <template v-else>
              Кампании не найдены
            </template>
          </TableEmpty>

          <TableRow
            v-for="campaign in campaigns"
            v-else
            :key="campaign.id"
            data-test="campaign-row"
          >
            <TableCell>{{ campaign.id }}</TableCell>

            <TableCell class="font-medium">
              {{ campaign.name }}
            </TableCell>

            <TableCell>{{ campaign.subject }}</TableCell>
            <TableCell>{{ campaign.fromName ?? '—' }}</TableCell>

            <TableCell>
              <Badge :variant="statusVariant(campaign.status)">
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
        </TableBody>
      </Table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';

import { Badge, type BadgeVariants } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableEmpty,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useCampaigns } from '@/composables/useCampaigns';
import type { CampaignStatus } from '@/apiService/campaigns/campaignsApiTypes';

const { campaigns, isLoading, error, load } = useCampaigns();

onMounted(load);

const STATUS_LABEL: Record<CampaignStatus, string> = {
  draft: 'Черновик',
  running: 'Запущена',
  paused: 'Пауза',
  done: 'Завершена',
  error: 'Ошибка',
};

const STATUS_VARIANT: Record<CampaignStatus, BadgeVariants['variant']> = {
  draft: 'outline',
  running: 'default',
  paused: 'secondary',
  done: 'secondary',
  error: 'destructive',
};

function statusLabel(status: CampaignStatus): string {
  return STATUS_LABEL[status];
}

function statusVariant(status: CampaignStatus): BadgeVariants['variant'] {
  return STATUS_VARIANT[status];
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
