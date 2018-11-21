#######################################################################################
# ssanova_palate.R                                
# functions for SSANOVA comparisons of tongue traces in polar coordinates using gss 
# Jeff Mielke						revised October 22, 2013
# Susan Lin and Matt Faytak			revised January 2015 (palate and printing func.)
#######################################################################################
#
# BASIC COMMAND TO GENERATE AN SSANOVA PLOT (IF 'phone' IS THE NAME OF YOUR FACTOR)
#  ss <- polar.ssanova(data, 'phone')
#
# BASIC COMMAND TO PLOT THE RAW DATA
#  show.traces(data)
#
# TO PLOT TO FILE, SEPARATING BY TWO DIFFERENT FACTORS (COLUMNS IN YOUR DATA FRAME):
#  cairo_pdf('my_ssanova_pdf.pdf', h=4.5, w=5, onefile=T)
#    ss.by.C <- polar.ssanova(data, 'consonant')
#    ss.by.V <- polar.ssanova(data, 'vowel')
#  dev.off()
#
# TO HIGHLIGHT RAW DATA FOR THE LEVEL ('I'):
#  show.traces(data, c('I'))
#
# DATA FILE SHOULD BE ORGANIZED LIKE THIS (MULTIPLE COLUMNS CAN BE USED INSTEAD OF word):
#
# word,token,X,Y
# dog,1,307,262
# dog,1,311,249
# dog,1,315,240
# dog,2,308,261
# dog,2,311,250
# dog,2,314,249
# cat,1,307,240
# dog,2,311,250
# dog,2,314,259
# ...
#
#######################################################################################
#
# polar.ssanova() ARGUMENTS (ALL OPTIONAL EXCEPT data):
#
#           data: your tongue tracings (minimally including columns X and Y and a
#                 column with a factor)
#       data.cat: the factor to use to categorize the data (defaults to 'word')
#          scale: how much to scale the axis values (e.g. to convert from pixels to 
#                 centimeters)
#  origin.method: how to choose the origin for calculating polar coordinates
#          debug: whether to generate the cartesian and non-transformed polar plots too
#       plotting: whether to plot anything (or just return the result of the test)
#           main: the main title for the plot
#        CI.fill: whether to indicate confidence intervals with shading (like ggplot) 
#                 or with dotted lines (like the earlier SSANOVA code).  
#                 Defaults to FALSE (dotted lines)
#       printing: if TRUE, different splines use different line types, so that the
#                 figure can be printed in black and white.
#           flip: whether to flip the Y values (useful for plotting data from images
#                 in cartesian coordinates, but ignored if using polar coordinates)
# cartesian.only: used by cart.ssanova()
#       is.polar: if TRUE, the data is already in polar coordinates
#         palate: if defined, uses a two-column DataFrame of X and Y coordinates
#                 to draw a palate trace.
#
#######################################################################################
#
#  cart.ssanova() SAME AS polar.ssanova() BUT DOESN'T USE POLAR COORDINATES
#
#######################################################################################
#
#   show.traces() ARGUMENTS (ALL OPTIONAL EXCEPT data): 
#
#           data: your tongue tracings (minimally including columns X and Y and a
#                 column with a factor)
#       data.cat: the factor to use to categorize the tongues (defaults to 'word')
#   to.highlight: a list of factor levels to plot while muting the other levels
#        to.plot: a list of factor levels to plot, excluding the rest (defaults to all)
#    token.label: the factor to use to identify individual tokens (defaults to 'token')
#           flip: whether to flip the Y values (useful for plotting data from images)
#           main: the main title for the plot
#       overplot: whether to add the traces to an existing plot
#       is.polar: if TRUE, the data is already in polar coordinates
#         origin: used if the data is in polar coordinates already
#
#######################################################################################

library(gss)

#CONVERT POLAR COORDINATES TO CARTESIAN COORDINATES
make.cartesian <- function(tr, origin=c(0,0)){    
    X <- apply(tr, 1, function(x,y) origin[1]-x[2]*cos(x[1]))
    Y <- apply(tr, 1, function(x,y) x[2]*sin(x[1])-origin[2])
    xy <- cbind(X, Y)
    return(xy)
}

#CONVERT CARTESIAN COORDINATES TO POLAR COORDINATES
make.polar <- function(data.xy, origin=c(0,0)){
    xy <- cbind(data.xy$X, data.xy$Y)
    all_r <- apply(xy, 1, function(x) sqrt((x[1]-origin[1])^2 + (x[2]-origin[2])^2))
    all_theta <- pi+apply(xy, 1, function(x,y) atan2(x[2]-origin[2], x[1]-origin[1]))
    data.tr <- data.xy
    data.tr$X <- all_theta
    data.tr$Y <- all_r
    return(data.tr)
}

#RESCALE DATA FROM PIXELS TO CENTIMETERS
us.rescale<-function(data, usscale, X='X', Y='Y'){
    data[,c(X)] <- data[,c(X)]*usscale
    data[,c(Y)] <- data[,c(Y)]*usscale
    data
}

#SELECT AN APPROPRIATE ORIGIN FOR THE DATA
select.origin <- function(Xs, Ys, method='xmean_ymin'){
    if (method=='xmean_ymin'){
        if (mean(Ys)>0){
            return(c(mean(Xs), max(Ys)*1.01))
        }else{
            return(c(mean(Xs), min(Ys)*1.01))
        }
    }
    if (method=='xmean_ymean'){
        return(c(mean(Xs), mean(Ys)))
    }
    return(c(mean(Xs), max(Ys)*1.01))
}

#PERFORM THE SSANOVA AND RETURN THE RESULTING SPLINES AND CONFIDENCE INTERVALS
#expand.grid + predict scheme based on http://www.ling.upenn.edu/~joseff/papers/fruehwald_ssanova.pdf
tongue.ss <- function(data, data.cat='word', flip=FALSE, length.out=1000, alpha=1.4){    
    if (flip==TRUE){
        data$Y <- -data$Y
    }
    data$tempword <- data[,data.cat]
    #print(summary(lm(Y ~ tempword * X, data=data)))
    ss.model <- ssanova(Y ~ tempword + X + tempword:X, data=data, alpha=alpha)
    ss.result <- expand.grid(X=seq(min(data$X), max(data$X), length.out=length.out), tempword=levels(data$tempword))
    ss.result$ss.Fit <- predict(ss.model, newdata=ss.result, se=T)$fit
    ss.result$ss.cart.SE  <- predict(ss.model, newdata=ss.result, se=T)$se.fit
    #print(names(ss.result))
    #print(aggregate(ss.Fit ~ tempword, FUN=mean, data=ss.result))
    #print(aggregate(ss.cart.SE ~ tempword, FUN=mean, data=ss.result))
    ss.result$ss.upper.CI.X <- ss.result$X
    ss.result$ss.upper.CI.Y <- ss.result$ss.Fit + 1.96*ss.result$ss.cart.SE
    ss.result$ss.lower.CI.X <- ss.result$X
    ss.result$ss.lower.CI.Y <- ss.result$ss.Fit - 1.96*ss.result$ss.cart.SE
    names(ss.result)[which(names(ss.result)=='tempword')] <- data.cat
    ss.result
}

#PLOT THE SSANOVA RESULTS
plot.tongue.ss <- function(ss.result, data.cat, palate=NULL, lwd=3, main='', CI.fill=FALSE, printing=FALSE, show.legend=T, plot.labels=c(main,'X','Y'),
                           overplot=FALSE, grayscale=FALSE, xlim=NULL, ylim=NULL){  
    n_categories <- length(levels(ss.result[,data.cat]))
    if (grayscale==TRUE){
    	Fit.palette <- gray((1:n_categories)/n_categories - 1/n_categories)
    		CI.palette <- gray((1:n_categories)/n_categories - 1/n_categories, alpha=0.25)
    }else{
    	Fit.palette <- rainbow(n_categories, v=0.75)
    	CI.palette <- rainbow(n_categories, alpha=0.25, v=0.75)
    }
    xrange = range(c(ss.result$X, ss.result$ss.lower.CI.X, ss.result$ss.upper.CI.X))
    yrange = range(c(ss.result$ss.Fit, ss.result$ss.lower.CI.Y, ss.result$ss.upper.CI.Y))
    
    if (!is.null(palate)) {
    	   xrange[1] <- min(xrange[1],min(palate[1]))
    	   xrange[2] <- max(xrange[2],max(palate[1]))
    	   yrange[1] <- min(yrange[1],min(palate[2]))
    	   yrange[2] <- max(yrange[2],max(palate[2]))
    }

    if (is.null(xlim)){
        xlim <- xrange
    }
    if (is.null(ylim)){
        ylim <- yrange
    }
    if (!overplot){
        plot(0, 0, xlim=xlim, ylim=ylim, xaxt="n", yaxt="n", xlab='',ylab='', main=plot.labels[1], type='n')
    }

    if (printing){
        for (i in 1:n_categories){
            w=levels(ss.result[,data.cat])[i]
            subdata <- ss.result[ss.result[,data.cat]==w,]
            #if (CI.fill==TRUE){
                polygon(c(subdata$ss.upper.CI.X, rev(subdata$ss.lower.CI.X)),
                        c(subdata$ss.upper.CI.Y, rev(subdata$ss.lower.CI.Y)),
                        col=CI.palette[i], border=F)
                #}else{
                #lines(subdata$ss.upper.CI.X, subdata$ss.upper.CI.Y, type='l', col=Fit.palette[i], lty=3)
                #lines(subdata$ss.lower.CI.X, subdata$ss.lower.CI.Y, type='l', col=Fit.palette[i], lty=3)
                #}
            lines(subdata$X, subdata$ss.Fit, type='l', col=Fit.palette[i], lwd=lwd, lty=i)
            }
        lines(palate,lwd=1)
        if (show.legend){
            #legend(xrange[1]+0.8*diff(xrange), yrange[1]+0.3*diff(yrange), c(levels(ss.result[,data.cat])), lwd=lwd, col=Fit.palette, lty=1:n_categories)
            legend(xlim[1]+0.8*diff(ylim), ylim[1]+0.3*diff(ylim), c(levels(ss.result[,data.cat])), lwd=lwd, col=Fit.palette, lty=1:n_categories)
        }
    }else{
        for (i in 1:n_categories){
            w=levels(ss.result[,data.cat])[i]
            subdata <- ss.result[ss.result[,data.cat]==w,]
            if (CI.fill==TRUE){
                polygon(c(subdata$ss.upper.CI.X, rev(subdata$ss.lower.CI.X)),
                        c(subdata$ss.upper.CI.Y, rev(subdata$ss.lower.CI.Y)),
                        col=CI.palette[i], border=F)
                }else{
                lines(subdata$ss.upper.CI.X, subdata$ss.upper.CI.Y, type='l', col=Fit.palette[i], lty=3)
                lines(subdata$ss.lower.CI.X, subdata$ss.lower.CI.Y, type='l', col=Fit.palette[i], lty=3)
                }
            lines(subdata$X, subdata$ss.Fit, type='l', col=Fit.palette[i], lwd=lwd)
            }
        lines(palate,lwd=1)
        if (show.legend){
            legend('bottomright', c(levels(ss.result[,data.cat])), lwd=lwd, col=Fit.palette)
        }
    }
}

guess.data.cat <- function(data, data.cat){
    
}

#PLOT THE ORIGINAL DATA
show.traces <- function(data, data.cat='word', to.highlight=c(''), to.plot=c(''), token.label='token', flip=TRUE, main='', overplot=FALSE, is.polar=FALSE, grayscale=FALSE, origin=c(0,0)){ 
    if (sum(!names(data)%in%c('token','X','Y'))==1 & !data.cat%in%names(data)){
        data.cat <- names(data)[!names(data)%in%c('token','X','Y')]
        warning(paste('Using column \"',data.cat,'" to group the data.\nTo avoid this warning, use "show.traces(data, \'',data.cat,'\')"',sep=''))
    }
    #print(data.cat)
    show.cat <- function(data, data.cat, w, col){
        subdata <- data[data[,data.cat]==w,]
        subdata[,token.label] <- factor(subdata[,token.label])
        tokens <- levels(subdata[,token.label])
        for (t in tokens){
            token <- subdata[subdata[,token.label]==t,]
            lines(token$X,token$Y,col=col)
        }
    }
    if (flip){
        data$Y <- -data$Y
    }
    if (is.polar){
        data[,c('X','Y')] <- make.cartesian(data[,c('X','Y')], origin=origin)
    }
    categories <- levels(data[,data.cat])
    n_categories <- length(categories)
    if (grayscale==TRUE){
    	trace.palette <- gray((1:n_categories)/n_categories - 1/n_categories)
    	ghost.palette <- gray((1:n_categories)/n_categories - 1/n_categories)
    }else{
   		trace.palette <- rainbow(n_categories, v=0.7)
    	ghost.palette <- rainbow(n_categories, v=0.7, alpha=0.1)
    }
    if (overplot==FALSE){
        plot(0,0,xlim=range(data$X), ylim=range(data$Y),xlab='X',ylab='Y', main=main)
    }
    for (i in 1:n_categories){
        w=levels(data[,data.cat])[i]
        if (w%in%to.plot >= mean(categories%in%to.plot)){
            if (w%in%to.highlight >= mean(categories%in%to.highlight)){
                show.cat(data, data.cat, w, col=trace.palette[i])
            }else{
                show.cat(data, data.cat, w, col=ghost.palette[i])
            }
        }
    }
    legend('bottomright', categories, lwd=1, col=trace.palette)
}

#CALCULATE AN SSANOVA IN POLAR COORDINATES AND THEN PLOT IT BACK IN CARTESIAN COORDINATES
polar.ssanova <- function(data, data.cat='word', palate=NULL, scale=1, origin.method='xmean_ymin', debug=FALSE, plotting=TRUE, main='', 
                          CI.fill=FALSE, printing=FALSE, flip=TRUE, cartesian.only=FALSE, is.polar=FALSE, show.legend=TRUE, 
                          plot.labels=c(main,'X','Y'), overplot=FALSE, grayscale=FALSE, xlim=NULL, ylim=NULL, lwd=3, alpha=1.4){
    if (sum(!names(data)%in%c('token','X','Y'))==1 & !data.cat%in%names(data)){
        data.cat <- names(data)[!names(data)%in%c('token','X','Y')]
        warning(paste('Using column \"',data.cat,'" to group the data.\nTo avoid this warning, use "polar.ssanova(data, \'',data.cat,'\')"',sep=''))
    }
    if (flip==TRUE){
        data$Y <- -data$Y
    }
    data.scaled <- us.rescale(data, scale)
    if (cartesian.only){
        ss.pol.cart <- tongue.ss(data.scaled, data.cat=data.cat, flip=flip, alpha=alpha)
        ss.cart <- ss.pol.cart
        ss.polar <- ss.pol.cart
    }else{
        if (is.polar){
            #origin <- select.origin(data.scaled$X, data.scaled$Y, method=origin.method)
            origin <- c(0,0)
            print (origin)
            data.polar <- data.scaled
        }else{
            origin <- select.origin(data.scaled$X, data.scaled$Y, method=origin.method)
            print(paste('origin is',paste(origin)))
            print(summary(data.scaled$Y))
            data.polar <- make.polar(data.scaled, origin)
        }
        ss.polar <- tongue.ss(data.polar, data.cat=data.cat, alpha=alpha)
        ss.pol.cart <- ss.polar
        ss.pol.cart[,c('X','ss.Fit')] <- make.cartesian(ss.polar[,c('X','ss.Fit')], origin=origin)
        ss.pol.cart[,c('ss.cart.SE')] <- NA
        ss.pol.cart[,c('ss.upper.CI.X','ss.upper.CI.Y')] <- make.cartesian(ss.polar[,c('ss.upper.CI.X','ss.upper.CI.Y')], origin=origin)
        ss.pol.cart[,c('ss.lower.CI.X','ss.lower.CI.Y')] <- make.cartesian(ss.polar[,c('ss.lower.CI.X','ss.lower.CI.Y')], origin=origin)
    }
    if (plotting){
        if (debug){
            ss.cart <- tongue.ss(data.scaled, data.cat=data.cat, flip=T)
            plot.tongue.ss(ss.cart, data.cat, palate=palate, main=main, CI.fill=CI.fill, printing=printing, show.legend=show.legend, plot.labels=plot.labels, overplot=overplot, grayscale=grayscale, xlim=xlim, ylim=ylim, lwd=lwd)
            plot.tongue.ss(ss.polar, data.cat, palate=palate, main=main, CI.fill=CI.fill, printing=printing, show.legend=show.legend, plot.labels=plot.labels, overplot=overplot, grayscale=grayscale, xlim=xlim, ylim=ylim, lwd=lwd)
        }
        plot.tongue.ss(ss.pol.cart, data.cat, palate=palate, main=main, CI.fill=CI.fill, printing=printing, show.legend=show.legend, plot.labels=plot.labels, overplot=overplot, grayscale=grayscale, xlim=xlim, ylim=ylim, lwd=lwd)
    }
    return(ss.pol.cart) 
}



#CALCULATE AN SSANOVA IN CARTESIAN COORDINATES (NOT ADVISED FOR ULTRASOUND DATA)
cart.ssanova <- function(data, data.cat='word', palate=NULL, scale=1, origin.method='xmean_ymin', debug=FALSE, plotting=TRUE, main='', 
                         CI.fill=FALSE, printing=FALSE, flip=TRUE, show.legend=TRUE, plot.labels=c(main,'X','Y'), overplot=FALSE, xlim=NULL, 
                         ylim=NULL, lwd=3, alpha=1.4){
    polar.ssanova(data=data, data.cat=data.cat, palate=NULL, scale=scale, origin.method=origin.method, debug=debug, plotting=plotting, main=main,
                  CI.fill=CI.fill, printing=printing, flip=flip, cartesian.only=TRUE, show.legend=show.legend, plot.labels=plot.labels, 
                  overplot=overplot, xlim=xlim, ylim=ylim, lwd=lwd, alpha=alpha)
}


