$(function() {
	const opacity = 'rgba(0, 0, 0, .6)';
	// Create the QuaggaJS config object for the live stream
	var liveStreamConfig = {
			inputStream: {
				type : "LiveStream",
				constraints: {
					width: {min: 640},
					height: {min: 480},
					aspectRatio: {min: 1, max: 100},
					facingMode: "environment" // or "user" for the front camera
				},
        area: { // defines rectangle of the detection/localization area
          top: "40%",    // top offset
          right: "20%",  // right offset
          left: "20%",   // left offset
          bottom: "40%"  // bottom offset
        }
			},
  			numOfWorkers: (navigator.hardwareConcurrency ? navigator.hardwareConcurrency : 4),
  			decoder: {
				readers: ["code_128_reader"],
        debug: {
          drawBoundingBox: true,
          showFrequency: false,
          drawScanline: true,
          showPattern: false
        }
			},
			locate: false
		};

	// Start the live stream scanner when the modal opens
	$('#livestream_scanner').on('shown.bs.modal', function (e) {
		Quagga.init(
			liveStreamConfig,
			function(err) {
				if (err) {
					$('#livestream_scanner .modal-body .error').html('<div class="alert alert-danger"><strong><i class="fa fa-exclamation-triangle"></i> '+err.name+'</strong>: '+err.message+'</div>');
					Quagga.stop();
					return;
				}
				Quagga.start();
			}
		);
    });

	// Make sure, QuaggaJS draws frames and lines around possible
	// barcodes on the live stream
	Quagga.onProcessed(function(result) {
		var drawingCtx = Quagga.canvas.ctx.overlay,
			  drawingCanvas = Quagga.canvas.dom.overlay;

		if (result) {
			if (result.boxes) {
				w = drawingCanvas.getAttribute("width");
				h = drawingCanvas.getAttribute("height");
				drawingCtx.clearRect(0, 0, parseInt(drawingCanvas.getAttribute("width")), parseInt(drawingCanvas.getAttribute("height")));
				result.boxes.filter(function (box) {
					return box !== result.box;
				}).forEach(function (box) {
					drawingCtx.fillStyle = opacity;
					drawingCtx.fillRect(0, 0, w, h);
					drawingCtx.clearRect(w/5, 2*h/5, 3*w/5, h/5)
					Quagga.ImageDebug.drawPath(box, {x: 0, y: 1}, drawingCtx, {color: "#fff", lineWidth: 1.5});
				});
			}

			/*if (result.box) {
				Quagga.ImageDebug.drawPath(result.box, {x: 0, y: 1}, drawingCtx, {color: "#00F", lineWidth: 2});
			}*/

			if (result.codeResult && result.codeResult.code) {
				Quagga.ImageDebug.drawPath(result.line, {x: 'x', y: 'y'}, drawingCtx, {color: 'red', lineWidth: 3});
			}
		}
	});

	// Once a barcode had been read successfully, stop quagga and
	// close the modal after a second to let the user notice where
	// the barcode had actually been found.
	Quagga.onDetected(function(result) {
		if (result.codeResult.code){
			$('#bcode').val(result.codeResult.code);
			Quagga.stop();
			setTimeout(function(){ $('#livestream_scanner').modal('hide'); }, 1000);
		}
	});

	// Stop quagga in any case, when the modal is closed
    $('#livestream_scanner').on('hide.bs.modal', function(){
    	if (Quagga){
    		Quagga.stop();
    	}
    });

	// Call Quagga.decodeSingle() for every file selected in the
	// file input
	$("#livestream_scanner input:file").on("change", function(e) {
		if (e.target.files && e.target.files.length) {
			Quagga.decodeSingle($.extend({}, fileConfig, {src: URL.createObjectURL(e.target.files[0])}), function(result) {alert(result.codeResult.code);});
		}
	});
});
