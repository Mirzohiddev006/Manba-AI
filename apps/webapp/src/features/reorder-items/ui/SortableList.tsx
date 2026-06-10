import { DndContext, closestCenter, type DragEndEvent } from '@dnd-kit/core';
import {
  SortableContext, arrayMove, useSortable, verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

import type { ListItem } from '@/entities/list';
import { haptic } from '@/shared/lib/telegram';

function Row({ item }: { item: ListItem }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: item.id });
  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className="flex items-start gap-2 rounded-xl bg-tg-secondary p-3"
      {...attributes}
      {...listeners}
    >
      <span className="cursor-grab text-tg-hint">⠿</span>
      <p className="text-sm text-tg-text">{item.source.formatted_text}</p>
    </div>
  );
}

export function SortableList({
  items, onReorder,
}: { items: ListItem[]; onReorder: (ids: number[]) => void }) {
  const onDragEnd = (e: DragEndEvent) => {
    const { active, over } = e;
    if (!over || active.id === over.id) return;
    haptic('light');
    const oldIdx = items.findIndex((i) => i.id === active.id);
    const newIdx = items.findIndex((i) => i.id === over.id);
    onReorder(arrayMove(items, oldIdx, newIdx).map((i) => i.id));
  };
  return (
    <DndContext collisionDetection={closestCenter} onDragEnd={onDragEnd}>
      <SortableContext items={items.map((i) => i.id)} strategy={verticalListSortingStrategy}>
        <div className="space-y-2">
          {items.map((item) => <Row key={item.id} item={item} />)}
        </div>
      </SortableContext>
    </DndContext>
  );
}
