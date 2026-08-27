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
          <TableHead>Действия</TableHead>
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
            <TableCell><Skeleton class="h-8 w-8 rounded-md" /></TableCell>
          </TableRow>
        </template>

        <template v-else>
          <TableEmpty
            v-if="props.campaigns.length === 0"
            :colspan="7"
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
              <RouterLink
                :to="{ name: 'campaign-details', params: { id: campaign.id } }"
                class="hover:underline"
                data-test="campaign-link"
              >
                {{ campaign.name }}
              </RouterLink>
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

            <TableCell>
              <Button
                :aria-label="`Удалить кампанию ${campaign.name}`"
                variant="ghost"
                size="icon"
                data-test="delete-button"
                @click="openDialog(campaign)"
              >
                <Trash class="h-4 w-4" />
              </Button>
            </TableCell>
          </TableRow>
        </template>
      </TableBody>
    </Table>

    <AlertDialog v-model:open="isDialogOpen">
      <AlertDialogContent data-test="delete-dialog">
        <AlertDialogHeader>
          <AlertDialogTitle>Удалить кампанию?</AlertDialogTitle>

          <AlertDialogDescription>
            Кампания «{{ pendingCampaign?.name }}» будет удалена вместе со всеми
            получателями и вложениями. Действие необратимо.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <Button
            :disabled="isDeleting"
            variant="outline"
            data-test="cancel-delete-button"
            @click="closeDialog"
          >
            Отмена
          </Button>

          <Button
            :disabled="isDeleting"
            variant="destructive"
            data-test="confirm-delete-button"
            @click="confirmDelete"
          >
            <LoaderCircle
              v-if="isDeleting"
              class="h-4 w-4 animate-spin"
            />

            {{ isDeleting ? 'Удаление…' : 'Удалить' }}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import { LoaderCircle, Trash } from '@lucide/vue';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
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
import useDeleteCampaign from '@/composables/data/useDeleteCampaign';
import useToast from '@/composables/useToast';

interface Props {
  campaigns?: Campaign[];
  isLoading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  campaigns: () => [],
  isLoading: false,
});

const emit = defineEmits<{ deleted: [] }>();

const toast = useToast();
const { isLoading: isDeleting, deleteCampaign, onDone } = useDeleteCampaign();

const pendingCampaign = ref<Campaign | null>(null);
const isDialogOpen = ref(false);

function openDialog(campaign: Campaign) {
  pendingCampaign.value = campaign;
  isDialogOpen.value = true;
}

function closeDialog() {
  isDialogOpen.value = false;
}

function confirmDelete() {
  if (!pendingCampaign.value) {
    return;
  }

  deleteCampaign({ id: pendingCampaign.value.id });
}

onDone(() => {
  toast.success('Кампания удалена');

  isDialogOpen.value = false;

  emit('deleted');
});

const STATUS_LABEL: Record<CampaignStatus, string> = {
  new: 'Новая',
  in_progress: 'В работе',
  done: 'Завершена',
  done_with_errors: 'Завершена с ошибками',
  error: 'Ошибка',
};

const STATUS_CLASS: Record<CampaignStatus, string> = {
  new: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  in_progress: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300',
  done: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  done_with_errors: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
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
