# Script and utility functions for parsing batch runs of geoclaw
# Andrew Kaluzny (akk2141@columbia.edu)
# May 5, 2015

library(R.matlab) #for reading the reference gauges

# helper function to extract regex matches from a character vector
regextract <- function(pattern, x, invert=FALSE) {
    return(regmatches(x, regexpr(pattern, x), invert=invert))
}

# extract information about cell counts at levels over time
# returns a list, with the ith element the sequence of cells counts at level i
parse_cells <- function(log_file) {
    log_lines <- readLines(log_file)
    cell_pattern <- "\\s*cells at level\\s*"
    cell_lines <- regextract(paste0("\\d+",cell_pattern,"\\d+"), log_lines)
    cell_text <- regextract(cell_pattern, cell_lines, invert=TRUE)
    cell_counts <- sapply(cell_text, as.integer)
    cells <- list()
    for (ii in 1:max(cell_counts[2,])) {
        cells[[ii]] <- cell_counts[1, cell_counts[2,] == ii]
    }
    return(cells)
}

# read in gauge data from a fort.gauge file, organize by gauge
# result is a list, with ith element the data for gauge i
read_gauges <- function(gauge_file) {
    raw_data <- read.table(gauge_file)
    n <- max(raw_data[,1])
    gauge_data <- list()
    for (ii in 1:n) {
        indices <- raw_data[,1] == ii
        frame <- data.frame(height=raw_data[indices, 7],
                            time=raw_data[indices, 3],
                            level=raw_data[indices, 2])
        gauge_data[[ii]] <- frame
    }
    return(gauge_data)
}

# helper function for testing purposes
plot_gauges <- function(gauge_data) {
    for (gauge in gauge_data) {
        plot(gauge$time, gauge$height, type="l")
    }
}


# helper function to make vectors for use in plotting cell counts as step functions
make_steps <- function(counts) {
    # make x values scaled to [0,1]
    x <- seq(0, 1, length.out=length(counts)+1)
    # interleave x, y coords with themselves to make the steps
    y <- interleave(counts, counts)
    x <- interleave(x, x[2:(length(x)-1)])
    return(list(x=x, y=y))
}

# helper function to interleave two vectors
# (idea from http://stackoverflow.com/questions/16443260/interleave-lists-in-r)
interleave <- function(x, y) {
    indices <- order(c(seq_along(x), seq_along(y)))
    return(c(x,y)[indices])
}
