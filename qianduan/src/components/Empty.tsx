import { toast } from "sonner";
import { cn } from "@/lib/utils";

// Empty component
export function Empty({ title, description }: { title?: string, description?: string }) {
  return (
    <div className={cn("flex flex-col h-full items-center justify-center py-12 text-center px-4")}>
      <div className="w-24 h-24 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-6">
        <i className="fas fa-leaf text-emerald-500 text-3xl opacity-50" />
      </div>
      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
        {title || "暂无数据"}
      </h3>
      <p className="text-gray-500 dark:text-gray-400 mb-6 max-w-md">
        {description || "没有找到相关内容"}
      </p>
      <button 
        onClick={() => toast('刷新数据中...')}
        className="px-4 py-2 bg-emerald-500 text-white rounded-full text-sm font-medium hover:bg-emerald-600 transition-colors"
      >
        刷新数据
      </button>
    </div>
  );
}