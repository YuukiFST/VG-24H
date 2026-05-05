import Scrim from '../../partial/js/behavior/scrim'

/**
 * Classe para o exemplo do comportamento Scrim
 */
class ScrimExample {
  /**
   * Instancia um exemplo de comportamento Scrim
   * scrimToInitialize array de id_or_classe_acionador:id_or_classe_scrim para inicializar
   */
  constructor({ arrayConfigScrim = [] }) {
    this.arrayConfigScrim = arrayConfigScrim
    this._setBehavior()
  }
  /**
   * Inicia comportamento do exemplo
   * @private
   */
  _setBehavior() {
    this._setScrimBehavior()
  }
  /**
   * Encontra o componentes .scrimutilsample button  e coloca no evento de click o scrim
   * @private
   */
  _setScrimBehavior() {
    this.arrayConfigScrim.forEach((item) => {
      for (const buttonActionScrim of window.document.querySelectorAll(item.trigger_open_scrim)) {
        buttonActionScrim.addEventListener('click', () => {
          this.openScrimExample(item)
        })
      }
    })
  }

  /**
   * Abre o scrim de id scrimutilexample
   */
  openScrimExample(item) {
    const scrscrim = window.document.querySelector(item.scrimid)
    const scrimfoco = new Scrim({
      closeElement: item.trigger_close_scrim,
      trigger: scrscrim,
      escEnable: true,
      limitTabKey: true,
    })
    scrimfoco.showScrim()
  }
}

export default ScrimExample
