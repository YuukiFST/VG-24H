/**
 * Classe que instancia os exemplos de uso dos utilitários
 */

import AccordionExample from '../../util/accordion/accordion'
import CheckgroupExample from '../../util/checkgroup/checkgroup'
import CollapseExample from '../../util/collapse/collapse'
import DropdownExample from '../../util/dropdown/dropdown'
import ScrimExample from '../../util/scrim/scrim'
import TooltipExample from '../../util/tooltip/tooltip'

export default class Behavior {
  initInstanceAll() {
    this._initInstanceAccordionExample()
    this._initInstanceCheckGroupExemple()
    this._initInstanceCollapseExample()
    this._initInstanceDropdownExample()
    this._initInstanceTooltipExample()
    this._initInstanceScrimExample()
  }

  _initInstanceCollapseExample() {
    const collapseExampleList = []
    window.document.querySelectorAll('.collapse-example').forEach((collapseExample) => {
      collapseExampleList.push(new CollapseExample(collapseExample))
    })
  }

  _initInstanceAccordionExample() {
    const accordionExampleList = []
    window.document.querySelectorAll('.accordion-example').forEach((accordionExample) => {
      accordionExampleList.push(new AccordionExample(accordionExample))
    })
  }

  _initInstanceCheckGroupExemple() {
    const checkgroupExampleList = []
    window.document.querySelectorAll('.checkgroup-example').forEach((checkgroupExample) => {
      checkgroupExampleList.push(new CheckgroupExample(checkgroupExample))
    })
  }

  _initInstanceDropdownExample() {
    const dropdownExampleList = []
    window.document.querySelectorAll('.dropdown-example').forEach((dropdownExample) => {
      dropdownExampleList.push(new DropdownExample(dropdownExample))
    })
  }

  _initInstanceScrimExample() {
    const initializeScrim = [
      {
        trigger_open_scrim: '#idbuttonscrimutil',
        scrimid: '#scrimutilexample',
      },
      {
        trigger_open_scrim: '#idbuttonscrimutil1',
        trigger_close_scrim: '#scrimfechar',
        scrimid: '#scrimutilfocobig',
      },
    ]
    const scrimExample = new ScrimExample({ arrayConfigScrim: initializeScrim })
  }
  _initInstanceTooltipExample() {
    const tooltipExample = new TooltipExample()
    tooltipExample.run()
  }
}
