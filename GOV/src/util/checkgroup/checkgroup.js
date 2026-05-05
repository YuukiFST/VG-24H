import Checkgroup from '../../partial/js/behavior/checkgroup'

/**
 * Classe para o exemplo do comportamento checkgroup
 */
class CheckgroupExample {
  /**
   * Instancia um exemplo de comportamento checkgroup
   * @param {object} element - Elemento DOM que representa um componente contento um comportamento de checkgroup
   */
  constructor(element) {
    this.element = element
    this._setBehavior()
  }
  /**
   * Inicia comportamento do exemplo
   * @private
   */
  _setBehavior() {
    this._setCheckgroupBehavior()
  }

  /**
   * Encontra os data-toggle checkbox  com data-parent e coloca util Checkgroup
   * @private
   */

  _setCheckgroupBehavior() {
    this.element.querySelectorAll('input[type="checkbox"][data-parent]').forEach((trigger) => {
      const checkgroup = new Checkgroup(trigger)
      checkgroup.setBehavior()
    })
  }
}

export default CheckgroupExample
