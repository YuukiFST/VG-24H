import Collapse from '../../partial/js/behavior/collapse'

/**
 * Classe para o exemplo do comportamento collapse
 */
class CollapseExample {
  /**
   * Instancia um exemplo de comportamento collapse
   * @param {object} element - Elemento DOM que representa um componente contento um comportamento de collapse
   */
  constructor(element) {
    this.element = element
    this._setBehavior()
  }
  /**
   * Instancia o utilitario
   * @private
   */
  _setBehavior() {
    this._setCollapseBehavior()
  }
  /**
   * Instancia o utilitario no data-toggle collapse
   * @private
   */
  _setCollapseBehavior() {
    this.element.querySelectorAll('[data-toggle="collapse"]').forEach((trigger) => {
      const config = {
        iconToHide: 'fa-chevron-up',
        iconToShow: 'fa-chevron-down',
        trigger,
        useIcons: true,
      }
      const collapse = new Collapse(config)
      collapse.setBehavior()
    })
  }
}

export default CollapseExample
