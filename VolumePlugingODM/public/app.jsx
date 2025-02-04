import L, { popup } from 'leaflet';
import './app.scss';
import 'leaflet-measure-ex/dist/leaflet-measure';
import 'leaflet-measure-ex/dist/leaflet-measure.css';
import MeasurePopup from './MeasurePopup';
import Utils from 'webodm/classes/Utils';
import ReactDOM from 'ReactDOM';
import React , { useEffect } from 'react';
import $ from 'jquery';
import { _, get_format } from 'webodm/classes/gettext';
import { unitSystem } from 'webodm/classes/Units';
import Dropzone from './dropzone';
import { JamToast } from './jam-toast';
import './jam-toast.css';
import {v4 as uuidv4} from 'uuid';

export default class App{
  constructor(map){
    const myToast = new JamToast({
      maxCount: 5,
      timeout: 5000,
      position: 'top-mid',
    });
    this.map = map;
    this.iTitle = _('Measurement Object');
    loadFile(window.location.href.match(/[a-f0-9\-]{36}/)[0])
    const measure = L.control.measure({
      labels:{
        measureDistancesAndAreas: _('Measure volume, area and length'),
        areaMeasurement: this.iTitle,
        measure: _("Measure"),
        createNewMeasurement: _("Create a new measurement"),
        startCreating: _("Start creating a measurement by adding points to the map"),
        finishMeasurement: _("Finish measurement"),
        lastPoint: _("Last point"),
        area: _("Area"),
        perimeter: _("Perimeter"),
        pointLocation: _("Point location"),
        linearMeasurement: _("Linear measurement"),
        pathDistance: _("Path distance"),
        centerOnArea: _("Center on this area"),
        centerOnLine: _("Center on this line"),
        centerOnLocation: _("Center on this location"),
        cancel: _("Cancel"),
        delete: _("Delete"),
        acres: _("Acres"),
        feet: _("Feet"),
        kilometers: _("Kilometers"),
        hectares: _("Hectares"),
        meters: _("Meters"),
        miles: _("Miles"),
        sqfeet: _("Sq Feet"),
        sqmeters: _("Sq Meters"),
        sqmiles: _("Sq Miles"),
        decPoint: get_format("DECIMAL_SEPARATOR"),
        thousandsSep: get_format("THOUSAND_SEPARATOR")
      },
      primaryLengthUnit: 'meters',
      secondaryLengthUnit: 'feet',
      primaryAreaUnit: 'sqmeters',
      secondaryAreaUnit: 'acres',
      baseMethod: 'custom',
      position: 'topleft',
      // polygon colors
      activeColor: 'yellow',
      completedColor: 'yellow',
      customValue: 0,
      importStatus: false,
      uniqueIdPolygon: '',

      shapeOptions: {
        color: 'palegreen',
        fillColor: 'red',
        fillOpacity: 0.5
      }
    }).addTo(map);
    measure.importStatus = false;

    const addDnDZone = (container, opts) => {
      const mapTempLayerDrop = new Dropzone(container, opts);
      mapTempLayerDrop.on("addedfile", (file) => {

        if (!file.name.endsWith(".geojson") && !file.type.includes("json")) {
          console.error("Le fichier n'est pas un GeoJSON valide.");
          myToast.showToast("Erreur : le fichier n'est pas un .GeoJSON", 'error');
          mapTempLayerDrop.removeFile(file);
          return;
        }

        const reader = new FileReader();
        reader.onload = (event) => {
          try {
            myToast.showToast('Fichier en cours d\'importation . . .', 'info');
            const content = event.target.result;
            const geojson = JSON.parse(content);
            if (importGeoJSONToMap(geojson) == 1) {
              myToast.showToast("Il n'y a pas de polygones valides ou save dans le fichier !", 'error');
            } else { 
              myToast.showToast('Fichier importé avec succès', 'success');
              }
          } catch (error) {
            console.error("Erreur lors de la lecture du fichier GeoJSON :", error);
            myToast.showToast("Erreur : le fichier n'est pas un GeoJSON valide.", 'error');
          }
        };

        reader.onerror = () => {
          console.error("Erreur lors de la lecture du fichier avec FileReader.");
          myToast.showToast("Erreur lors de lecture du fichier, veuillez réessayer", 'error');
        };

        reader.readAsText(file);
      });
      mapTempLayerDrop.on("error", (file) => {
        mapTempLayerDrop.removeFile(file);
      });
    };

    const AddOverlayCtrl = L.Control.extend({
      options: {
          position: 'topleft'
      },
  
      onAdd: function () {
        this.container = L.DomUtil.create('div', 'leaflet-control-add-overlay leaflet-bar leaflet-control');
        L.DomEvent.disableClickPropagation(this.container);
        const btn = L.DomUtil.create('a', 'leaflet-control-add-overlay-button');
        btn.setAttribute("title", _("Add a temporary GeoJSON (.json) or ShapeFile (.zip) overlay"));
        this.container.append(btn);
        addDnDZone(btn, {url: "/", clickable: true});
        return this.container;
      }
    });
    new AddOverlayCtrl().addTo(this.map);

    function saveFunctionnality () {
      if (!window.location.href.match(/[a-f0-9\-]{36}/)[0]) {
        myToast.showToast("Erreur : aucun fichier ne peut être enregistré sur une carte qui englobe plusieur projet !", 'error');
      } else {
        saveFile(window.location.href.match(/[a-f0-9\-]{36}/)[0])
      }
    };

    const AddOverlaySaveBtn = L.Control.extend({
      options: {
          position: 'topleft'
      },
  
      onAdd: function () {
        this.container = L.DomUtil.create('div', 'leaflet-control-add-overlay-for-save leaflet-bar leaflet-controll');
        L.DomEvent.disableClickPropagation(this.container);
        const btn = L.DomUtil.create('a', 'leaflet-control-add-overlay-for-save-button');
        btn.setAttribute("title", _("Save all the polygons into a file for further utilisation"));
        this.container.append(btn);
        // Attach the click event to the button
        L.DomEvent.on(btn, 'click', function (e) {
          L.DomEvent.stopPropagation(e); // Prevent map click events
          L.DomEvent.preventDefault(e); // Prevent default behavior like link navigation

          saveFunctionnality(); // Call your addSave function
        });
        return this.container;
      }
    });
    new AddOverlaySaveBtn().addTo(this.map);

    function clearAllLayer() {
      myToast.showToast("Suppresion de toutes les formes de la map . . .", 'info');
      map.eachLayer(layer => {
        if (layer instanceof L.Polygon || layer instanceof L.GeoJSON) {
          map.removeLayer(layer);
        }
      });
    }

    const AddOverlayClearBtn = L.Control.extend({
      options: {
          position: 'topleft'
      },
  
      onAdd: function () {
        this.container = L.DomUtil.create('div', 'leaflet-control-add-overlay-for-save leaflet-bar leaflet-control');
        L.DomEvent.disableClickPropagation(this.container);
        const btn = L.DomUtil.create('a', 'leaflet-control-add-overlay-for-clear-button');
        btn.setAttribute("title", _("testnumero2svpfonctionnebrother"));
        this.container.append(btn);
        L.DomEvent.on(btn, 'click', function (e) {
          L.DomEvent.stopPropagation(e);
          L.DomEvent.preventDefault(e); 
          clearAllLayer(); 
        });
        return this.container;
      }
    });
    new AddOverlayClearBtn().addTo(this.map);

    measure._getMeasurementDisplayStrings = measurement => {
      const us = unitSystem();

      return {
        lengthDisplay: us.length(measurement.length).toString(),
        areaDisplay: us.area(measurement.area).toString()
      };
    };

    const $btnExport = $(`<br/><a href='#' class='js-start start'>${_("Export Measurements")}</a>`);
    $btnExport.appendTo($(measure.$startPrompt).children("ul.tasks"));
    $btnExport.on('click', () => {
      saveFile(null)
    });

    function saveFile(id) {
      const features = [];
      map.eachLayer(layer => {
          const mp = layer._measurePopup;
          if (mp) {
              const geoJSONFeature = mp.getGeoJSON();
              if (mp.props.model) {
                  geoJSONFeature.properties = {
                      ...geoJSONFeature.properties,
                      Title: mp.props.model.title,
                      Color: mp.props.model.color,
                      UniqueIdPolygon: mp.props.model.uniqueIdPolygon
                  };
              }
              features.push(geoJSONFeature);
          }
      });

      const geoJSON = {
          type: "FeatureCollection",
          TaskID: id,
          fsf: getName(),
          features: features
      };

      if (id != null) {
        const backendUrl = `/api/plugins/VolumePlugingODM/task/file/save/${id}`;
        const externalApiUrl = `http://localhost:3000/add/scraps/geojson/${getName().split(" / ")[0].toLowerCase()}`;

        Promise.all([
          sendGeoJSON(backendUrl, geoJSON),
          sendGeoJSON(externalApiUrl, geoJSON)
        ]).then(([backendResponse, externalResponse]) => {
          if (!backendResponse['error'] && !externalResponse['error']) {
            myToast.showToast('Les infos ont été sauvegardées avec succès sur les deux serveurs', 'success');
          } else {
            myToast.showToast("Un problème est survenu pendant la sauvegarde", 'error');
          }
        }).catch(error => {
          myToast.showToast("Erreur lors de la sauvegarde : " + error.message, 'error');
        });
      } else {
        Utils.saveAs(JSON.stringify(geoJSON, null, 4), "measurements.geojson");
      }
    }

    function sendGeoJSON(url, data) {
      return $.ajax({
        type: 'POST',
        url: url,
        data: JSON.stringify(data),
        contentType: "application/json"
      });
    }

    function loadFile(id) {
      if (!id) {
        myToast.showToast('Erreur : aucun fichier ne peut être enregistré sur une carte qui englobe plusieur projet !', 'error');
        return
      }
      myToast.showToast('Chargement des informations en cours . . .', 'info');
      const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));
      (async () => {
        await wait(4000);
        $.ajax({
          type: 'GET',
          url: `http://localhost:3000/get/scraps/geojson/${getName().split(" / ")[0].toLowerCase()}/${id}`,
          contentType: "application/json"
        }).done(result => {
          if (!result['error']) {
            if (importGeoJSONToMap(result) == 1) {
              myToast.showToast("Le fichier n'est pas valide", 'error');
            } else { 
              myToast.showToast('Fichier importé avec succès', 'success');
              }
          } else {
            myToast.showToast("Il n'y a pas de polygon enregistré sur cette map", 'error');
          }
        })
      })();
    }

    map.on('measurestart', (e) => {
      measure.options.labels.areaMeasurement = 'Measurement Object';
      // Prompt for title before measurement starts
      // const title = ("Measuremente");
      // this.iTitle = _(title || 'Measurement Object');

      // measure.options.labels.areaMeasurement = this.iTitle;
      // measure.options.activeColor = 'palegreen';
      // measure.options.completedColor = 'yellow';
      // measure.completedColor = 'palegreen';
      // measure.activeColor = 'yellow';
      // console.log("ON MEASURE START", measure.activeColor, measure.completedColor)


      // const randomColor = getRandomColor();
      
      // Update the style of existing layers (if necessary)
      // map.on('measure:drawstart', function (drawEvent) {
      //   drawEvent.layer.setStyle({
      //       color: randomColor,
      //       fillColor: randomColor,
      //       fillOpacity: 0.5
      //   });
      // });

      // Apply new style to any existing layers (if needed)
      // map.eachLayer(function (layer) {
      //   if (layer instanceof L.Polygon) {
      //       layer.setStyle({
      //           color: randomColor,
      //           fillColor: randomColor,
      //           fillOpacity: 0.5
      //       });
      //   }
      // });

    });

    map.on('measurepopupshown', ({popupContainer, model, resultFeature}) => {
        if (measure.importStatus == false) {
          measure.activeColor = 'yellow';
          measure.completedColor = 'yellow';
          measure.customValue = 0;
          measure.uniqueIdPolygon = "";
        }
        model.color = measure.activeColor
        if (measure.uniqueIdPolygon == "") {
          model.uniqueIdPolygon = uuidv4();
        } else {
          model.uniqueIdPolygon = measure.uniqueIdPolygon;
        }
        // Only modify area popup, length popup is fine as default
        const $container = $("<div/>"),
              $popup = $(popupContainer);
        if (model.area !== 0){
          $popup.children("p").empty();
        }
        $popup.children("h3").empty();

        let $popupFeatures = $('<div />').attr('style', 'display: flex; flex-direction: column; align-items: left; gap: 10px;');
        if (!measure.activeColor) { measure.activeColor = 'yellow'; }
        const $dropdown = $(`
          <div class="dropdown">
              <div id="main-color" class="main-color" style="background-color: ${measure.activeColor};"></div>
              <div class="dropdown-menu" id="dropdown-menu">
                  <div class="color-option" style="background-color: #e74c3c;" data-color="#e74c3c"></div>
                  <div class="color-option" style="background-color: #2ecc71;" data-color="#2ecc71"></div>
                  <div class="color-option" style="background-color: #f1c40f;" data-color="#f1c40f"></div>
                  <div class="color-option" style="background-color: #9b59b6;" data-color="#9b59b6"></div>
                  <div class="color-option" style="background-color: #3498db;" data-color="#3498db"></div>

              </div>
          </div>
        `); 
        
        $popupFeatures.prepend($dropdown);
        
        const $mainColor = $dropdown.find('#main-color');
        const $dropdownMenu = $dropdown.find('#dropdown-menu');
        
        $mainColor.on('click', () => {
          $dropdownMenu.toggleClass('open');
        });
        
        $dropdownMenu.on('click', '.color-option', (e) => {
          const $selected = $(e.target);
          const selectedColor = $selected.data('color');
          $mainColor.css('background-color', selectedColor);

          resultFeature.setStyle({
            color: selectedColor,
            fillColor: selectedColor,
          })

          if (model) {
            model.color = selectedColor;
          }
        
          // Ferme le dropdown
          $dropdownMenu.removeClass('open');
        });

        if (model && model.color) {
            model.color = measure.activeColor;
        }

        const $customHeader = $(`<input style="margin: auto auto 0 0;" type="text" id="titleInput" value="${measure.options.labels.areaMeasurement}" />`);
        $popupFeatures.prepend($customHeader);
        $customHeader.on('change', (e) => {
          const newTitle = $(e.target).val();
          this.iTitle = _(newTitle || 'Measurement Object');
          measure.options.labels.areaMeasurement = this.iTitle;
          if (model) {
            model.title = this.iTitle;
          }
          $customHeader.find("#titleInput").val(this.iTitle);
        });

        $popup.prepend($popupFeatures)

        $popup.children("ul.tasks").before($container);
        model.title = measure.options.labels.areaMeasurement;
        let areaPolygon = 0;
        if (model.area == 0) {
          areaPolygon = model.lengthDisplay;
        } else {
          areaPolygon = model.areaDisplay;
        }
        
        resultFeature.bindTooltip(areaPolygon, {
          permanent: true,   
          direction: 'center', 
          className: 'styleMeasureMap' 
        });
        
        resultFeature.setStyle({
          color: measure.activeColor,
          fillColor: measure.activeColor,
        })

        bringLinesToFront()

        ReactDOM.render(<MeasurePopup 
                            model={model}
                            resultFeature={resultFeature} 
                            map={map} 
                            title={this.iTitle}
                            baseMethod={measure.baseMethod} 
                            customValue={measure.customValue} />, $container.get(0));
    });
    
    function bringLinesToFront() {
      map.eachLayer(layer => {
        const mp = layer._measurePopup;

        if (mp) {
            const geoJSONFeature = mp.getGeoJSON();
            if (mp.props.model) {
                if (geoJSONFeature.geometry.type == 'LineString') {
                  layer.bringToFront();
                }
            }
        }
    });
    }

    function importGeoJSONToMap(geoJSONData) {
      if (!geoJSONData || !geoJSONData.features || geoJSONData.features.length === 0) {
          return 1;
      }

      geoJSONData.features.forEach(feature => {
          const geometry = feature.geometry;
          const properties = feature.properties || {};
          let latlngs = []
          if (geometry.type === "Polygon") {
              latlngs = geometry.coordinates[0].map(coord => L.latLng(coord[1], coord[0]));
          } else if (geometry.type === "LineString") {
              latlngs = geometry.coordinates.map(coord => L.latLng(coord[1], coord[0]));
          } else if (geometry.type === "Point") {
              latlngs = L.latLng(geometry.coordinates[1], geometry.coordinates[0]);
          } else {
              console.log("Unsupported geometry type:", geometry.type);
              return;
          }
          measure._startMeasure();
          if (latlngs.length === 1 || !latlngs.length) {
            measure._latlngs.push(latlngs);
            const vertex = L.circleMarker(latlngs, measure._symbols.getSymbol('measureVertex'));
            measure._measureVertexes.addLayer(vertex);
          } else {
            latlngs.forEach(latlng => {
              measure._latlngs.push(latlng);
              const vertex = L.circleMarker(latlng, measure._symbols.getSymbol('measureVertex'));
              measure._measureVertexes.addLayer(vertex);
            });
          }
          measure.options.labels.areaMeasurement = properties.Title;
          measure.baseMethod = properties.BaseSurface;
          measure.importStatus = true
          if (properties.Color) {measure.activeColor = properties.Color;}
          else if (!properties.Color) {measure.activeColor = 'yellow'}
          if (properties.CustomValue) {measure.customValue = properties.CustomValue;}
          else if (!properties.CustomValue) {measure.customValue = 0}
          if (properties.UniqueIdPolygon) {measure.uniqueIdPolygon = properties.UniqueIdPolygon;}
          else if (!properties.UniqueIdPolygon) {measure.uniqueIdPolygon = ''}
          measure._updateMeasureStartedWithPoints();
          measure._handleMeasureDoubleClick();
      });
      measure.importStatus = false
      measure.activeColor = 'yellow';
      measure.customValue = 0;
      measure.uniqueIdPolygon = ''
    }

    function getName() {
      for (let l in map._layers){
        const layer = map._layers[l];
        if (layer.options && layer.options.bounds){
          const symbols = Object.getOwnPropertySymbols(layer);
          const metaSymbol = symbols.find(sym => sym.toString() === "Symbol(meta)");
          
          if (metaSymbol) {
              const meta = layer[metaSymbol];
              return meta.task.name
          } else {
              console.log("Symbol(meta) non trouvé pour cette couche.");
          }
        }
      }
    }
  }
}





// $.ajax({
//   type: 'POST',
//   url: `/api/plugins/VolumePlugingODM/task/file/load/${id}`,
//   data: JSON.stringify({
//     name: id,
//   }),
//   contentType: "application/json"
// }).done(result => {
//   if (!result['error']) {
//     importGeoJSONToMap(result['geoJSON'])
//     myToast.showToast('Chargement des informations reussi !', 'success');
//     return
//   } else {
//     myToast.showToast("Il n'y a pas de polygon enregistré sur cette map", 'error');
//   }
// })
// })();