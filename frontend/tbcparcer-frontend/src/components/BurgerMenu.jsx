import { useEffect } from 'react'
import { X, BarChart3, Plus, Settings, MessageSquare, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button.jsx'

const BurgerMenu = ({ isOpen, onClose, onAction }) => {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const menuItems = [
    {
      id: 'overview',
      icon: BarChart3,
      title: 'Обзор',
      description: 'Статистика и аналитика транзакций'
    },
    {
      id: 'add',
      icon: Plus,
      title: 'Добавить чек',
      description: 'Ручное добавление транзакции'
    },
    {
      id: 'trash',
      icon: Trash2,
      title: 'Корзина',
      description: 'Удаленные транзакции'
    },
    {
      id: 'settings',
      icon: Settings,
      title: 'Настройки',
      description: 'Конфигурация системы'
    },
    {
      id: 'telegram',
      icon: MessageSquare,
      title: 'Открыть Telegram-бота',
      description: 'Перейти к боту для парсинга чеков'
    }
  ]

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40 transition-opacity"
        onClick={onClose}
      />
      
      {/* Menu */}
      <div className="fixed top-0 left-0 h-full w-80 bg-card border-r border-border z-50 transform transition-transform">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border">
            <h2 className="text-lg font-semibold text-foreground">Меню</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="p-2"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
          
          {/* Menu Items */}
          <div className="flex-1 p-6">
            <nav className="space-y-2">
              {menuItems.map((item) => {
                const Icon = item.icon
                return (
                  <button
                    key={item.id}
                    onClick={() => onAction(item.id)}
                    className="w-full flex items-start space-x-3 p-3 rounded-lg hover:bg-muted/50 transition-colors text-left group"
                  >
                    <div className="flex-shrink-0 mt-0.5">
                      <Icon className="h-5 w-5 text-muted-foreground group-hover:text-foreground transition-colors" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium text-foreground group-hover:text-foreground transition-colors">
                        {item.title}
                      </h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        {item.description}
                      </p>
                    </div>
                  </button>
                )
              })}
            </nav>
          </div>
          
          {/* Footer */}
          <div className="p-6 border-t border-border">
            <div className="text-xs text-muted-foreground">
              <p className="font-medium">TBCparcer v3.0</p>
              <p className="mt-1">Система учета финансовых чеков</p>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

export default BurgerMenu

