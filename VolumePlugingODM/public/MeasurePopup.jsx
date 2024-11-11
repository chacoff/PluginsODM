import React from 'react';
import PropTypes from 'prop-types';
import './MeasurePopup.scss';
import Utils from 'webodm/classes/Utils';
import Workers from 'webodm/classes/Workers';
import { _, interpolate } from 'webodm/classes/gettext';
import { systems, unitSystem, getUnitSystem } from 'webodm/classes/Units';
import $ from 'jquery';
import L from 'leaflet';

export default class MeasurePopup extends React.Component {
  static defaultProps = {
    map: {}, 
    model: {},
    resultFeature: {},
    title: "volume object"
  };

  static propTypes = {
    map: PropTypes.object.isRequired,
    model: PropTypes.object.isRequired,
    resultFeature: PropTypes.object.isRequired,
    title: PropTypes.string.isRequired
  }

  constructor(props){
    super(props);

    let featureType = "Point";
    if (props.model.area !== 0) featureType = "Polygon";
    else if (props.model.length > 0) featureType = "LineString";

    this.state = {
        featureType,
        volume: null, // to be calculated,
        baseMethod: localStorage.getItem("measure_base_method") || "triangulate",
        task: null,
        error: "",
        customValue: 0,
        isAbsoluteVolume: false,
        title: props.title, // title available at this stage
    };

    this.exportMeasurement = this.exportMeasurement.bind(this);
    this.getProperties = this.getProperties.bind(this);
    this.getGeoJSON = this.getGeoJSON.bind(this);

    // this.handleBaseMethodChange = this.handleBaseMethodChange.bind(this);
    // this.handleCustomValueChange = this.handleCustomValueChange.bind(this);
    this.handleKeyDown = this.handleKeyDown.bind(this);
    this.handleCheckboxChange = this.handleCheckboxChange.bind(this);
  }

  componentDidMount(){
    if (this.state.featureType == "Polygon") this.calculateVolume();
    this.props.resultFeature._measurePopup = this;
  }

  componentWillUnmount(){
    this.props.resultFeature._measurePopup = null;
  }

  getProperties(){
    const us = systems[this.lastUnitSystem];

    const result = {
      Length: us.length(this.props.model.length).value,
      Area: us.area(this.props.model.area).value,
      Title: this.state.title 
    };
    
    if (this.state.volume !== null && this.state.volume !== false){
        result.Volume = us.volume(this.state.volume).value;
        result.BaseSurface = this.state.baseMethod;
    }

    result.UnitSystem = this.lastUnitSystem;
    
    return result;
  }

  getGeoJSON(){
    const geoJSON = this.props.resultFeature.toGeoJSON();
    geoJSON.properties = this.getProperties();
    return geoJSON;
  }

  exportMeasurement(){
    const geoJSON = {
      type: "FeatureCollection",
      features: [this.getGeoJSON()]
    };

    Utils.saveAs(JSON.stringify(geoJSON, null, 4), "measurement.geojson")
  }

  handleBaseMethodChange = (e) => {
    this.setState({baseMethod: e.target.value});
    localStorage.setItem("measure_base_method", e.target.value);
    setTimeout(() => {
      this.recalculateVolume();
    }, 0);
  }

  handleCustomValueChange = (e) => {
    this.setState({ customValue: e.target.value });
  }

  handleKeyDown(e) {
    if (e.key === 'Enter') {
      console.log('Custom Value Changed:', e.target.value);
      setTimeout(() => {
        this.recalculateVolume();
      }, 0);
    }
  }
  
  handleCheckboxChange(e) {
    this.setState({ isAbsoluteVolume: e.target.checked });
    console.log(e.target.checked);
    setTimeout(() => {
      this.recalculateVolume();
    }, 0);
  }

  calculateVolume(){
    const { lastCoord } = this.props.model;
    let layers = this.getLayersAtCoords(L.latLng(
            lastCoord.dd.y,
            lastCoord.dd.x
        ));

    // Did we select a layer?
    if (layers.length > 0){
        const layer = layers[layers.length - 1];
        const meta = layer[Symbol.for("meta")];
        if (meta){
            this.setState({task: meta.task});
            setTimeout(() => {
              this.recalculateVolume();
            }, 0);
        }else{
            console.warn("Cannot find [meta] symbol for layer: ", layer);
            this.setState({volume: false});
        }
    }else{
        this.setState({volume: false});
    }
  }

  recalculateVolume = () => {
    const { task, baseMethod , customValue, isAbsoluteVolume} = this.state;
    if (!task) return;

    this.setState({volume: null, error: ""});

    $.ajax({
        type: 'POST',
        url: `/api/plugins/VolumePlugingODM/task/${task.id}/volume`,
        data: JSON.stringify({
          area: this.props.resultFeature.toGeoJSON(),
          method: baseMethod,
          base: customValue,
          isAbsolute: isAbsoluteVolume
        }),
        contentType: "application/json"
    }).done(result => {
        if (result.celery_task_id){
            Workers.waitForCompletion(result.celery_task_id, error => {
              if (error) this.setState({error});
              else{
                  Workers.getOutput(result.celery_task_id, (error, volume) => {
                    console.log(volume);
                      if (error) this.setState({error});
                      else this.setState({volume: parseFloat(volume)});
                  }, `/api/plugins/VolumePlugingODM/task/${task.id}/volume/get/`);
              }
            }, `/api/plugins/VolumePlugingODM/task/${task.id}/volume/check/`);
        }else if (result.error){
            this.setState({error: result.error});
        }else{
            this.setState({error: interpolate(_("Invalid response: %(error)s"), { error: result})});
        }
    }).fail(error => {
        this.setState({error});
    });
  }

  // @return the layers in the map
    //      at a specific lat/lon
  getLayersAtCoords(latlng){
    const targetBounds = L.latLngBounds(latlng, latlng);

    const intersects = [];
    for (let l in this.props.map._layers){
        const layer = this.props.map._layers[l];

        if (layer.options && layer.options.bounds){
            if (targetBounds.intersects(layer.options.bounds)){
                intersects.push(layer);
            }
        }
    }

    return intersects;
  }

  render(){
    const { volume, error, featureType, baseMethod, customValue, isAbsoluteVolume, title } = this.state;
    const us = unitSystem();
    this.lastUnitSystem = getUnitSystem();

    const baseMethods = [
      {label: _("Triangulate"), method: 'triangulate'},
      {label: _("Plane"), method: 'plane'},
      {label: _("Average"), method: 'average'},
      {label: _("Highest"), method: 'highest'},
      {label: _("Lowest"), method: 'lowest'},
      {label: _("Custom"), method: 'custom'}
    ];

    return (<div className="plugin-measure popup">
        <p>{_("Name:")}<input type="text" className="form-control" /></p>
        {featureType == "Polygon" && <p>{_("Perimeter:")} {this.props.model.lengthDisplay}</p>}
        {featureType == "Polygon" && <p>{_("Area:")} {this.props.model.areaDisplay}</p>}
        {featureType == "Polygon" && volume === null && !error && <p>{_("Volume:")} <i>{_("computing…")}</i> <i className="fa fa-cog fa-spin fa-fw" /></p>}
        {typeof volume === "number" ? 
            [
              <p>{_("Volume:")} {us.volume(volume).toString()}</p>,
              <p className="base-control">{_("Base surface:")} 
                <select className="form-control" value={this.state.baseMethod} onChange={this.handleBaseMethodChange}>
                  {baseMethods.map(bm => 
                      <option key={bm.method} 
                              value={bm.method}>{bm.label}</option>)}
                </select>
              </p>,

              baseMethod === 'custom' && (
              <p className="base-control">{_("Custom Value:")}
                <input type="number" className="form-control" value={this.state.customValue} onChange={this.handleCustomValueChange} onKeyDown={this.handleKeyDown}>
                </input>
              </p>
              ),

              <p>{_("Absolute Volume:")} <input type="checkbox" checked={this.state.isAbsoluteVolume} onChange={this.handleCheckboxChange} /></p>

            ]
        : ""}
        {error && <p>{_("Volume:")} <span className={"error theme-background-failed " + (error.length > 200 ? 'long' : '')}>{error}</span></p>}
        
        <a href="#" className="export-measurements" style={{ cursor: 'not-allowed' }}><i className="fa fa-database"></i> {_("Export to DB")}</a>
        
        <a href="#" onClick={this.exportMeasurement} className="export-measurements"><i className="fa fa-download"></i> {_("Export to GeoJSON")}</a>

    </div>);
  }
}