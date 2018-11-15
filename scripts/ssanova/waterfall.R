require(ggplot2)

# waterfall.R: plot "waterfall" diagrams of contours in a time series, using color to encode time.
# Intended for use directly on the .con file format that EdgeTrak outputs.
# Simply read in the .con file as a data frame; make sure to set header=FALSE.
# usage: ultrawf(contour_data_frame, "Title of plot")

ultrawf <- function(con,main){
	ncols = dim(con)[2]
	xmax = max(con[,c(seq(1,ncols,2))])
	xmin = min(con[,c(seq(1,ncols,2))])
	ymax = max(con[,c(seq(1,ncols,2)+1)])
	ymin = min(con[,c(seq(1,ncols,2)+1)])
	idx = 0
	seed <- ggplot(data=con,aes(x=con[,1], y=con[,2], color=idx)) + 
				geom_path(lwd=1) +
				xlim(xmax,xmin) +
				ylim(ymax,ymin) +
				labs(title=main) +
				xlab("X") + 
				ylab("Y") +
				scale_color_distiller(type="div", palette = "RdBu")
	nframes = ncols/2
	for(i in 1:nframes){
		xin <- 2*i-1
		yin <- 2*i
		idx = idx + 1
		gg.data <- data.frame(x=con[,xin],y=con[,yin],idx=rep(idx,100))
		seed <- seed + geom_path(data=gg.data, aes(x=x, y=y, color=idx), lwd=1)
	}
	mid = ceiling(nframes/2)
	xmid = 2*mid-1
	ymid = 2*mid
	gg.data <- data.frame(x=con[,xmid], y=con[,ymid])
	seed <- seed + geom_path(data=gg.data, aes(x=x, y=y), color="black", lwd=1, lty=3)
	return(seed)
}