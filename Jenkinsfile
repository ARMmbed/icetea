echo "Start to build"


properties ([
    buildDiscarder(
        logRotator(
            artifactDaysToKeepStr: '',
            artifactNumToKeepStr: '',
            daysToKeepStr: '30',
            numToKeepStr: '100'
        )
    )
])


timestamps {
    timeout(time: 30, unit: "MINUTES") {
        parallel(
            "stream linux": {
                node('linux') {
                    deleteDir()
                    dir("icetea"){
                        stage("Checkout linux source") {
                            echo "hello world!"
                            checkout scm
                        }

                        def pipeline = load "pipeline.groovy"

                        pipeline.baseBuild('linux')
                    }

                    // clean up
                    step([$class: 'WsCleanup'])
                }
            },
            "stream windows": {
                node('windows') {
                    deleteDir()
                    dir("icetea"){
                        stage("Checkout windows source") {
                            echo "hello world!"
                            checkout scm
                        }

                        def pipeline = load "pipeline.groovy"

                        pipeline.baseBuild('windows')
                    }

                    // clean up
                    step([$class: 'WsCleanup'])
                }
            },
            "stream example cliapp": {
                node('arm-none-eabi-gcc') {
                    deleteDir()
                    try {
                        dir("icetea"){
                            def pipeline = null
                            stage ("deploy") {
                                checkout scm
                                pipeline = load "pipeline.groovy"
                            }

                            if (pipeline) {
                                pipeline.buildExampleApp()
                            }
                        }
                    } catch (err) {
                        throw err
                    } finally {
                        // clean up
                        step([$class: 'WsCleanup'])
                    }
                }
            },
            "stream linux-e2e-local-hw-tests": {
                node('oul_ext_lin_nuc') {
                    deleteDir()
                    try {
                        dir("icetea"){
                            def pipeline = null
                            stage ("checkout linux-nuc source") {
                                def scmVars = checkout scm
                                env.GIT_COMMIT_HASH = scmVars.GIT_COMMIT

                                pipeline = load "pipeline.groovy"
                            }

                            if (pipeline) {
                                pipeline.runLinuxHwTests()
                            }
                        }
                    } catch (err) {
                        throw err
                    } finally {
                        // clean up
                        //step([$class: 'WsCleanup'])
                    }


                }
            },
            "stream win-e2e-local-hw-tests": {
                node('oul_ext_win_flasher_nuc') {
                    deleteDir()
                    try {
                        dir("icetea"){
                            def pipeline = null
                            stage ("checkout win-nuc source") {
                                def scmVars = checkout scm
                                env.GIT_COMMIT_HASH = scmVars.GIT_COMMIT

                                pipeline = load "pipeline.groovy"
                            }

                            if (pipeline) {
                                pipeline.runWinHwTests()
                            }
                        }
                    } catch (err) {
                        throw err
                    } finally {
                        // clean up
                        //step([$class: 'WsCleanup'])
                    }


                }
            }
        )
    }
}
