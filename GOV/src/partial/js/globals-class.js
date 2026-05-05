// Script Templates
import BRAccordion from '../../components/accordion/accordion'
import BRAvatar from '../../components/avatar/avatar'
import BRBreadcrumb from '../../components/breadcrumb/breadcrumb'
import BRCard from '../../components/card/card'
import BRCarousel from '../../components/carousel/carousel'
import BRCheckbox from '../../components/checkbox/checkbox'
import BRCookiebar from '../../components/cookiebar/cookiebar'
import jsonData from '../../components/cookiebar/jsonData' // dados para instanciação do cookiebar
import BRDateTimePicker from '../../components/datetimepicker/datetimepicker'
import BRFooter from '../../components/footer/footer'
import BRHeader from '../../components/header/header'
import BRInput from '../../components/input/input'
import inputData from '../../components/input/input-data' // Dados para o autocomplete do input
import BRItem from '../../components/item/item'
import BRList from '../../components/list/list'
import BRMenu from '../../components/menu/menu'
import BRMessage from '../../components/message/message'
import BRModal from '../../components/modal/modal'
import BRNotification from '../../components/notification/notification'
import BRPagination from '../../components/pagination/pagination'
import BRScrim from '../../components/scrim/scrim'
import BRSelect from '../../components/select/select'
import BRStep from '../../components/step/step'
import BRTab from '../../components/tab/tab'
import BRTable from '../../components/table/table'
import BRTag from '../../components/tag/tag'
import BRTextarea from '../../components/textarea/textarea'
import BRTooltip from '../../components/tooltip/tooltip'
import BRUpload from '../../components/upload/upload'
import BRWizard from '../../components/wizard/wizard'
import Accordion from './behavior/accordion'
import Checkgroup from './behavior/checkgroup'
import Collapse from './behavior/collapse'
import Dropdown from './behavior/dropdown'
import Scrim from './behavior/scrim'
import Swipe from './behavior/swipe'

export default class Globals {
  initInstanceAll() {
    this.initInstanceAccordion()
    this.initInstanceAvatar()
    this.initInstanceBreadcrumb()
    this.initInstanceCard()
    this.initInstanceCarousel()
    this.initInstanceCheckbox()
    this.initInstanceCookiebar()
    this.initInstanceDateTimePicker()
    this.initInstanceFooter()
    this.initInstanceInput()
    this.initInstanceHeader()
    this.initInstanceItem()
    this.initInstanceList()
    this.initInstanceMenu()
    this.initInstanceMessage()
    this.initInstanceModal()
    this.initInstanceNotification()
    this.initInstancePagination()
    this.initInstanceScrim()
    this.initInstanceSelect()
    this.initInstanceStep()
    this.initInstanceTable()
    this.initInstanceTabs()
    this.initInstanceTextarea()
    this.initInstanceUpload()
    this.initInstanceWizard()
    this.initInstanceTooltip()
  }

  initInstanceAccordion() {
    const accordionList = []
    for (const brAccordion of window.document.querySelectorAll('.br-accordion')) {
      accordionList.push(new BRAccordion('br-accordion', brAccordion))
    }
  }

  initInstanceAvatar() {
    const avatarList = []
    for (const brAvatar of window.document.querySelectorAll('.br-avatar')) {
      avatarList.push(new BRAvatar('br-avatar', brAvatar))
    }
  }

  initInstanceBreadcrumb() {
    const breadcrumbList = []
    for (const brBreadcrumb of window.document.querySelectorAll('.br-breadcrumb')) {
      breadcrumbList.push(new BRBreadcrumb('br-breadcrumb', brBreadcrumb))
    }
  }

  initInstanceDateTimePicker() {
    const datetimepickerList = []
    for (const brDateTimePicker of window.document.querySelectorAll('.br-datetimepicker')) {
      datetimepickerList.push(new BRDateTimePicker('br-datetimepicker', brDateTimePicker, {}))
    }
  }

  initInstanceHeader() {
    const headerList = []
    for (const brHeader of window.document.querySelectorAll('.br-header')) {
      headerList.push(new BRHeader('br-header', brHeader))
    }
  }
  initInstanceFooter() {
    const listFooter = []
    for (const brFooter of window.document.querySelectorAll('.br-footer')) {
      listFooter.push(new BRFooter('br-footer', brFooter))
    }
  }

  initInstanceInput() {
    const inputList = []
    for (const brInput of window.document.querySelectorAll('.br-input')) {
      inputList.push(new BRInput('br-input', brInput))
    }
    for (const brInput of inputList) {
      brInput.component.querySelectorAll('input.search-autocomplete').forEach(() => {
        brInput.setAutocompleteData(inputData)
      })
    }
  }

  initInstanceItem() {
    const itemList = []
    for (const brItem of window.document.querySelectorAll('.br-item')) {
      itemList.push(new BRItem('br-item', brItem))
    }
  }

  initInstanceList() {
    const listList = []
    for (const brList of window.document.querySelectorAll('.br-list:not([data-sub])')) {
      listList.push(new BRList('br-list', brList))
    }
  }

  initInstanceMenu() {
    const menuList = []
    for (const brMenu of window.document.querySelectorAll('.br-menu')) {
      menuList.push(new BRMenu('br-menu', brMenu))
    }
  }

  initInstanceMessage() {
    const alertList = []
    for (const brMessage of window.document.querySelectorAll('.br-message')) {
      alertList.push(new BRMessage('br-message', brMessage))
    }
  }

  initInstanceModal() {
    const buttonActivateModalScrim = window.document.querySelector('#buttonactivatemodal')
    if (buttonActivateModalScrim) {
      const scrscrim = window.document.querySelector('#scrimutilexamplemodal')

      const scrimfoco = new Scrim({
        trigger: scrscrim,
        escEnable: true,
        limitTabKey: true,
      })
      buttonActivateModalScrim.addEventListener('click', (event) => {
        scrimfoco.showScrim()
      })
    }
  }

  initInstanceNotification() {
    const notificationList = []
    for (const brNotification of window.document.querySelectorAll('.br-notification')) {
      notificationList.push(new BRNotification('br-notification', brNotification))
    }
  }

  initInstancePagination() {
    const paginationList = []
    for (const brPagination of window.document.querySelectorAll('.br-pagination')) {
      paginationList.push(new BRPagination('br-pagination', brPagination))
    }
  }

  initInstanceScrim() {
    const scrimList = []
    for (const brScrim of window.document.querySelectorAll('.br-scrim')) {
      scrimList.push(new BRScrim('br-scrim', brScrim))
    }
    for (const buttonBloco1 of window.document.querySelectorAll('.bloco1 button')) {
      buttonBloco1.addEventListener('click', () => {
        for (const brScrim of scrimList) {
          brScrim.showScrim()
        }
      })
    }
  }

  initInstanceSelect() {
    const selectList = []
    for (const brSelect of window.document.querySelectorAll('.br-select')) {
      const brselect = new BRSelect('br-select', brSelect)
      //Exemplo de uso de listener do select
      // brSelect.addEventListener('onChange', () => {})

      selectList.push(brselect)
    }
  }

  initInstanceTable() {
    const tableList = []
    for (const [index, brTable] of window.document.querySelectorAll('.br-table').entries()) {
      tableList.push(new BRTable('br-table', brTable, index))
    }
  }

  initInstanceTag() {
    const tagList = []
    for (const brTag of window.document.querySelectorAll('.br-tag')) {
      tagList.push(new BRTag('br-tag', brTag))
    }
  }

  initInstanceTabs() {
    const abasList = []
    for (const brTab of window.document.querySelectorAll('.br-tab')) {
      abasList.push(new BRTab('br-tab', brTab))
    }
  }

  initInstanceTooltip() {
    const tooltipList = []
    for (const brTooltip of window.document.querySelectorAll('.br-tooltip')) {
      tooltipList.push(new BRTooltip('br-tooltip', brTooltip))
    }
  }

  initInstanceUpload() {
    const uploadList = []
    function uploadTimeout() {
      return new Promise((resolve) => {
        // Colocar aqui um upload para o servidor e retirar o timeout
        return setTimeout(resolve, 500)
      })
    }
    for (const brUpload of window.document.querySelectorAll('.br-upload')) {
      uploadList.push(new BRUpload('br-upload', brUpload, uploadTimeout))
    }
  }

  initInstanceStep() {
    const stepList = []
    for (const brStep of window.document.querySelectorAll('.br-step')) {
      stepList.push(new BRStep('br-step', brStep))
    }
  }

  initInstanceCard() {
    const listCard = []
    for (const brCard of window.document.querySelectorAll('.br-card')) {
      listCard.push(new BRCard('br-card', brCard))
    }
  }
  initInstanceCarousel() {
    const carouselList = []
    for (const brCarousel of window.document.querySelectorAll('.br-carousel')) {
      carouselList.push(new BRCarousel('br-carousel', brCarousel))
    }
  }

  initInstanceCheckbox() {
    const checkboxList = []
    for (const brCheckbox of window.document.querySelectorAll('.br-checkbox')) {
      checkboxList.push(new BRCheckbox('br-checkbox', brCheckbox))
    }
  }

  initInstanceCookiebar() {
    /** Exemplo de instanciação de um objeto cookiebar */
    const cookiebarList = []
    for (const brCookiebar of window.document.querySelectorAll('.br-cookiebar')) {
      const params = {
        // callback: (outputJSON) => { console.log(JSON.parse(outputJSON)) console.log(outputJSON) },
        component: brCookiebar,
        json: jsonData,
        lang: 'pt-br',
        mode: 'default',
        name: 'br-cookiebar',
      }
      // CookiebarData.loadJSON('./data.json', (response) => {
      //   return (params.json = response)
      // })
      cookiebarList.push(new BRCookiebar(params))
    }

    /** Exemplo de instanciação do cookibar apenas sem necessidade de um HTML base */
    // BRCookiebar.createCookiebar(jsonData, showOutput)
  }

  initInstanceTextarea() {
    const textareaList = []
    for (const brTextarea of window.document.querySelectorAll('.br-textarea')) {
      textareaList.push(new BRTextarea('br-textarea', brTextarea))
    }
  }
  initInstanceWizard() {
    const wizardList = []
    for (const brWizard of window.document.querySelectorAll('.br-wizard')) {
      wizardList.push(new BRWizard('br-wizard', brWizard))
    }
  }
}

export {
  Accordion,
  BRAccordion,
  BRAvatar,
  BRBreadcrumb,
  BRCard,
  BRCheckbox,
  BRCookiebar,
  BRDateTimePicker,
  BRFooter,
  BRHeader,
  BRInput,
  BRItem,
  BRList,
  BRMenu,
  BRMessage,
  BRModal,
  BRNotification,
  BRPagination,
  BRScrim,
  BRSelect,
  BRTab,
  BRTable,
  BRTag,
  BRTextarea,
  BRTooltip,
  BRUpload,
  BRWizard,
  Checkgroup,
  Collapse,
  Dropdown,
  Globals,
  Scrim,
  Swipe,
}
