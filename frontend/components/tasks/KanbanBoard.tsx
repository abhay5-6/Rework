"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { 
  DndContext, 
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay,
  DragStartEvent,
  DragOverEvent,
  DragEndEvent,
  defaultDropAnimationSideEffects
} from '@dnd-kit/core';
import { 
  SortableContext, 
  arrayMove, 
  sortableKeyboardCoordinates,
  verticalListSortingStrategy
} from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { getWorkspaceTasks, updateTask, Task } from '@/lib/api/tasks';
import { User, Clock, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';
import { useDroppable } from '@dnd-kit/core';

interface KanbanBoardProps {
  roomId: number;
  currentUsername: string;
}

// Columns definition
const COLUMNS = [
  { id: 'todo', title: 'To Do' },
  { id: 'in_progress', title: 'In Progress' },
  { id: 'done', title: 'Done' }
];

export default function KanbanBoard({ roomId, currentUsername }: KanbanBoardProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);

  const loadTasks = useCallback(async () => {
    try {
      const data = await getWorkspaceTasks(roomId);
      // Map completed_at to status for older tasks if necessary
      const normalizedData = data.map(t => ({
        ...t,
        status: t.status || (t.completed_at ? 'done' : 'todo')
      }));
      setTasks(normalizedData);
    } catch (error) {
      console.error("Failed to load tasks", error);
    }
  }, [roomId]);

  useEffect(() => {
    void Promise.resolve().then(loadTasks);
    const interval = setInterval(loadTasks, 5000);
    
    const handleUpdate = () => loadTasks();
    window.addEventListener("task_update", handleUpdate);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener("task_update", handleUpdate);
    };
  }, [loadTasks]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  function handleDragStart(event: DragStartEvent) {
    setActiveId(String(event.active.id));
  }

  function handleDragOver(event: DragOverEvent) {
    const { active, over } = event;
    if (!over) return;

    const activeId = String(active.id);
    const overId = String(over.id);

    if (activeId === overId) return;

    const isActiveTask = active.data.current?.type === 'Task';
    const isOverTask = over.data.current?.type === 'Task';
    const isOverColumn = over.data.current?.type === 'Column';

    if (!isActiveTask) return;

    // Dropping a Task over another Task
    if (isActiveTask && isOverTask) {
      setTasks((tasks) => {
        const activeIndex = tasks.findIndex((t) => String(t.id) === activeId);
        const overIndex = tasks.findIndex((t) => String(t.id) === overId);

        if (tasks[activeIndex].status !== tasks[overIndex].status) {
          const newTasks = [...tasks];
          newTasks[activeIndex].status = tasks[overIndex].status;
          return arrayMove(newTasks, activeIndex, overIndex);
        }

        return arrayMove(tasks, activeIndex, overIndex);
      });
    }

    // Dropping a Task over a column empty area
    if (isActiveTask && isOverColumn) {
      setTasks((tasks) => {
        const activeIndex = tasks.findIndex((t) => String(t.id) === activeId);
        const newTasks = [...tasks];
        newTasks[activeIndex].status = overId;
        return arrayMove(newTasks, activeIndex, activeIndex);
      });
    }
  }

  async function handleDragEnd(event: DragEndEvent) {
    setActiveId(null);
    const { active, over } = event;
    if (!over) return;

    const activeId = String(active.id);
    const overId = String(over.id);

    const activeTask = tasks.find((t) => String(t.id) === activeId);
    if (!activeTask) return;

    const targetStatus = over.data.current?.type === 'Column' 
      ? overId 
      : tasks.find((t) => String(t.id) === overId)?.status;

    if (targetStatus && targetStatus !== activeTask.status) {
      try {
        await updateTask(roomId, activeTask.id, { status: targetStatus });
        if (targetStatus === 'done') {
          toast.success("Task moved to Done!");
        }
      } catch {
        toast.error("Failed to move task");
        loadTasks(); // Revert
      }
    }
  }

  const activeTask = activeId ? tasks.find(t => String(t.id) === activeId) : null;

  return (
    <div className="flex h-full w-full gap-4 p-4 overflow-x-auto bg-black/40">
      <DndContext 
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        {COLUMNS.map((col) => (
          <KanbanColumn 
            key={col.id} 
            column={col} 
            tasks={tasks.filter(t => t.status === col.id)} 
            currentUsername={currentUsername}
          />
        ))}

        <DragOverlay dropAnimation={{ sideEffects: defaultDropAnimationSideEffects({ styles: { active: { opacity: "0.4" } } }) }}>
          {activeTask ? (
            <KanbanCard task={activeTask} currentUsername={currentUsername} isOverlay />
          ) : null}
        </DragOverlay>
      </DndContext>
    </div>
  );
}

// ==========================================
// COLUMN COMPONENT
// ==========================================

interface KanbanColumnProps {
  column: { id: string, title: string };
  tasks: Task[];
  currentUsername: string;
}

function KanbanColumn({ column, tasks, currentUsername }: KanbanColumnProps) {
  const { setNodeRef } = useDroppable({
    id: column.id,
    data: {
      type: 'Column',
      column,
    },
  });

  return (
    <div 
      className="flex flex-col flex-shrink-0 w-[300px] bg-zinc-900/60 border border-white/5 rounded-2xl overflow-hidden"
    >
      <div className="p-3 border-b border-white/5 bg-zinc-900 flex items-center justify-between">
        <h3 className="font-semibold text-zinc-200 text-sm">{column.title}</h3>
        <span className="bg-black/50 text-zinc-400 text-xs px-2 py-1 rounded-full font-medium">
          {tasks.length}
        </span>
      </div>
      
      <div 
        ref={setNodeRef}
        className="flex-1 p-3 overflow-y-auto flex flex-col gap-3 min-h-[150px]"
      >
        <SortableContext items={tasks.map(t => String(t.id))} strategy={verticalListSortingStrategy}>
          {tasks.map(task => (
            <SortableCard key={task.id} task={task} currentUsername={currentUsername} />
          ))}
        </SortableContext>
      </div>
    </div>
  );
}

// ==========================================
// CARD COMPONENTS
// ==========================================

function SortableCard({ task, currentUsername }: { task: Task, currentUsername: string }) {
  const {
    setNodeRef,
    attributes,
    listeners,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: String(task.id),
    data: {
      type: 'Task',
      task,
    },
  });

  const style = {
    transition,
    transform: CSS.Transform.toString(transform),
  };

  if (isDragging) {
    return (
      <div 
        ref={setNodeRef}
        style={style}
        className="bg-card/30 border-2 border-blue-500/50 border-dashed rounded-xl h-[100px] opacity-30"
      />
    );
  }

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <KanbanCard task={task} currentUsername={currentUsername} />
    </div>
  );
}

function KanbanCard({ task, currentUsername, isOverlay = false }: { task: Task, currentUsername: string, isOverlay?: boolean }) {
  const isMine = task.assignee_username === currentUsername;
  
  return (
    <div 
      className={`
        p-3 rounded-xl cursor-grab active:cursor-grabbing text-sm
        transition-colors
        ${isOverlay ? 'bg-zinc-800 shadow-2xl rotate-2 scale-105 border border-white/20' : 'bg-card hover:bg-card/80 border border-white/5'}
      `}
    >
      <div className="flex gap-2 items-start mb-2">
        {task.status === 'done' ? (
          <CheckCircle2 size={16} className="text-emerald-500 mt-0.5 shrink-0" />
        ) : (
          <div className="w-4 h-4 rounded-full border border-zinc-600 mt-0.5 shrink-0" />
        )}
        <p className={`text-zinc-200 leading-snug ${task.status === 'done' ? 'opacity-60 line-through' : ''}`}>
          {task.description}
        </p>
      </div>

      <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/5">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Clock size={12} />
          {new Date(task.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
        </div>
        
        {task.assignee_username && (
          <div className={`
            flex items-center gap-1 text-[10px] font-medium px-2 py-1 rounded-md
            ${isMine ? 'bg-blue-500/20 text-blue-400' : 'bg-zinc-800 text-zinc-400'}
          `}>
            <User size={10} />
            {isMine ? 'You' : task.assignee_username}
          </div>
        )}
      </div>
    </div>
  );
}
