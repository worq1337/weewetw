import { useState, useRef, useEffect } from 'react'
import { AlignLeft, AlignCenter, AlignRight } from 'lucide-react'
import { Button } from '@/components/ui/button.jsx'

const ColumnSettings = ({ settings, onSettingsChange, onClose }) => {
  const [alignment, setAlignment] = useState(settings.alignment || 'left')
  const dropdownRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        onClose()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [onClose])

  useEffect(() => {
    setAlignment(settings.alignment || 'left')
  }, [settings.alignment])

  const handleAlignmentChange = (newAlignment) => {
    setAlignment(newAlignment)
    onSettingsChange({
      ...settings,
      alignment: newAlignment
    })
  }

  const alignmentOptions = [
    { value: 'left', icon: AlignLeft, label: 'По левому краю' },
    { value: 'center', icon: AlignCenter, label: 'По центру' },
    { value: 'right', icon: AlignRight, label: 'По правому краю' }
  ]

  return (
    <div
      ref={dropdownRef}
      className="absolute top-full left-0 mt-1 bg-card border border-border rounded-md shadow-lg z-50 min-w-48"
    >
      <div className="p-3">
        <div className="mb-3">
          <h4 className="text-sm font-medium text-foreground mb-2">
            Выравнивание текста
          </h4>
          <div className="grid grid-cols-3 gap-1">
            {alignmentOptions.map((option) => {
              const IconComponent = option.icon

              return (
                <Button
                key={option.value}
                variant={alignment === option.value ? "default" : "outline"}
                size="sm"
                className="h-8 w-full"
                onClick={() => handleAlignmentChange(option.value)}
                title={option.label}
              >
                <IconComponent className="h-3 w-3" />
              </Button>
              )
            })}
          </div>
        </div>
        
        <div className="border-t border-border pt-3">
          <h4 className="text-sm font-medium text-foreground mb-2">
            Цвет фона ячеек
          </h4>
          <div className="grid grid-cols-6 gap-1">
            {[
              '#ffffff', '#f3f4f6', '#e5e7eb', '#d1d5db',
              '#fef3c7', '#fed7aa', '#fecaca', '#ddd6fe',
              '#c7d2fe', '#bfdbfe', '#a7f3d0', '#bbf7d0'
            ].map((color) => (
              <button
                key={color}
                className="w-6 h-6 rounded border border-border hover:scale-110 transition-transform"
                style={{ backgroundColor: color }}
                onClick={() => {
                  // Здесь можно добавить логику для изменения цвета ячеек
                  console.log('Selected color:', color)
                }}
                title={color}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ColumnSettings

