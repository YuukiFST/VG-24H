import Tooltip from '../../partial/js/behavior/tooltip'

/**
 * Classe de exemplo do comportamento tooltip
 */
class TooltipExample {
  /**
   * Instancia um exemplo de comportamento tooltip
   * @param {object} element - Elemento sDOM que representa um componente contento um comportamento de tooltip
   */
  constructor(element) {
    this.element = element
  }
  /**
   * Inicia comportamento do exemplo
   * @private
   */
  _setBehavior() {
    this.TooltipExampleList = []
  }

  /**
   * Encontra os data-tooltip-text  e coloca util Tooltip
   * @private
   */

  run() {
    this.TooltipExampleList = []

    window.document.querySelectorAll('[data-tooltip-text]:not(.notification-tooltip)').forEach((TooltipExample) => {
      const texttooltip = TooltipExample.getAttribute('data-tooltip-text')
      const config = {
        activator: TooltipExample,
        place: 'top',
        textTooltip: texttooltip,
      }
      this.TooltipExampleList.push(new Tooltip(config))
    })

    document.querySelectorAll('[data-tooltip-target]').forEach((trigger) => {
      const targets = document.querySelectorAll(trigger.getAttribute('data-tooltip-target'))

      targets.forEach((target) => {
        const place = target.getAttribute('place') !== null ? target.getAttribute('place') : 'left'

        const config = {
          activator: trigger,
          component: target,
          place: place,
          type: 'warning',
        }
        // const tooltip = new Tooltip(config)
        new Tooltip(config)
      })
    })
  }
}

export default TooltipExample
