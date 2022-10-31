package com.myspace.vibrations;

/**
 * This class was automatically generated by the data modeler tool.
 */

public class Part implements java.io.Serializable {

	static final long serialVersionUID = 1L;

	@org.kie.api.definition.type.Label(value = "id")
	private java.lang.String id;
	@org.kie.api.definition.type.Label(value = "machine_id")
	private java.lang.String machine_id;
	@org.kie.api.definition.type.Label(value = "vibration_level_1")
	private java.lang.Integer vibration_level_1;
	@org.kie.api.definition.type.Label(value = "vibration_level_2")
	private java.lang.Integer vibration_level_2;
	@org.kie.api.definition.type.Label(value = "vibration_level_3")
	private java.lang.Integer vibration_level_3;
	@org.kie.api.definition.type.Label(value = "quality_class")
	private java.lang.String quality_class;
	@org.kie.api.definition.type.Label(value = "timestamp")
	private java.lang.String timestamp;

	public Part() {
	}

	public java.lang.String getId() {
		return this.id;
	}

	public void setId(java.lang.String id) {
		this.id = id;
	}

	public java.lang.String getMachine_id() {
		return this.machine_id;
	}

	public void setMachine_id(java.lang.String machine_id) {
		this.machine_id = machine_id;
	}

	public java.lang.Integer getVibration_level_1() {
		return this.vibration_level_1;
	}

	public void setVibration_level_1(java.lang.Integer vibration_level_1) {
		this.vibration_level_1 = vibration_level_1;
	}

	public java.lang.Integer getVibration_level_2() {
		return this.vibration_level_2;
	}

	public void setVibration_level_2(java.lang.Integer vibration_level_2) {
		this.vibration_level_2 = vibration_level_2;
	}

	public java.lang.Integer getVibration_level_3() {
		return this.vibration_level_3;
	}

	public void setVibration_level_3(java.lang.Integer vibration_level_3) {
		this.vibration_level_3 = vibration_level_3;
	}

	public java.lang.String getQuality_class() {
		return this.quality_class;
	}

	public void setQuality_class(java.lang.String quality_class) {
		this.quality_class = quality_class;
	}

	public java.lang.String getTimestamp() {
		return this.timestamp;
	}

	public void setTimestamp(java.lang.String timestamp) {
		this.timestamp = timestamp;
	}

	public Part(java.lang.String id, java.lang.String machine_id,
			java.lang.Integer vibration_level_1,
			java.lang.Integer vibration_level_2,
			java.lang.Integer vibration_level_3,
			java.lang.String quality_class, java.lang.String timestamp) {
		this.id = id;
		this.machine_id = machine_id;
		this.vibration_level_1 = vibration_level_1;
		this.vibration_level_2 = vibration_level_2;
		this.vibration_level_3 = vibration_level_3;
		this.quality_class = quality_class;
		this.timestamp = timestamp;
	}

}